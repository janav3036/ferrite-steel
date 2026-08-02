import json

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from quotations.models import Lead
from credit_risk.models import CreditAssessment
from .forms import BrokerForm, CustomerForm, ProductForm
from .models import Broker, Customer, Product


@login_required
def product_list(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    unit = request.GET.get('unit', '').strip()
    status = request.GET.get('status', 'active').strip()

    products = Product.objects.select_related('base_product').order_by('category', 'item_no')

    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)
    # status == 'all' → no filter

    if q:
        products = products.filter(
            Q(item_no__icontains=q) |
            Q(product_name__icontains=q) |
            Q(hsn_code__icontains=q)
        )

    if category:
        if category == 'none':
            products = products.filter(category='')
        else:
            products = products.filter(category=category)

    if unit:
        products = products.filter(unit=unit)

    total_count = products.count()

    paginator = Paginator(products, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    querystring = request.GET.copy()
    querystring.pop('page', None)

    return render(request, 'database/product_list.html', {
        'page_obj': page_obj,
        'total_count': total_count,
        'q': q,
        'category': category,
        'unit': unit,
        'status': status,
        'category_choices': Product.CATEGORY_CHOICES,
        'unit_choices': Product.UNIT_CHOICES,
        'querystring': querystring.urlencode(),
    })


@login_required
def product_catalog_json(request):
    products = Product.objects.filter(is_active=True).select_related('base_product')
    data = [
        {
            'id': p.pk,
            'item_no': p.item_no,
            'product_name': p.product_name,
            'hsn_code': p.hsn_code,
            'category': p.get_category_display(),
            'unit': p.get_unit_display(),
            'quantity': str(p.quantity),
            'rate': str(p.effective_rate),
        }
        for p in products
    ]
    return JsonResponse({'products': data})


@login_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully.')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'database/product_add.html', {'form': form})


@login_required
def customer_search_json(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    customers = Customer.objects.filter(
        Q(name__icontains=q) | Q(company__icontains=q)
    ).order_by('name')[:15]
    results = [
        {'id': c.pk, 'name': c.name, 'company': c.company,
         'phone': c.phone, 'email': c.email, 'location': c.city or ''}
        for c in customers
    ]
    return JsonResponse({'results': results})


@login_required
def customer_list(request):
    scope = request.GET.get('scope', 'team')
    q = request.GET.get('q', '').strip()
    team_f = request.GET.get('team', '')
    payment_f = request.GET.get('payment_terms', '')
    biz_f = request.GET.get('type_of_business', '')
    if scope == 'all' or request.user.role == 'admin':
        qs = Customer.objects.all()
    elif request.user.team:
        qs = Customer.objects.filter(handling_team=request.user.team)
    else:
        qs = Customer.objects.none()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(company__icontains=q) | Q(customer_code__icontains=q))
    if team_f:
        qs = qs.filter(handling_team=team_f)
    if payment_f:
        qs = qs.filter(payment_terms=payment_f)
    if biz_f:
        qs = qs.filter(type_of_business=biz_f)
    params = request.GET.copy()
    params.pop('page', None)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    elided = [None if r == paginator.ELLIPSIS else r for r in paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)]
    return render(request, 'database/customer_list.html', {
        'page_obj': page_obj,
        'elided_page_range': elided,
        'scope': scope,
        'q': q,
        'team_f': team_f,
        'payment_f': payment_f,
        'biz_f': biz_f,
        'query_string': params.urlencode(),
        'team_choices': Customer.TEAM_CHOICES,
        'payment_choices': Customer.PAYMENT_TERMS_CHOICES,
        'biz_choices': Customer.TYPE_OF_BUSINESS_CHOICES,
    })


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    leads = Lead.objects.filter(
        customer_name__iexact=customer.name,
        company__iexact=customer.company,
    ).order_by('-created_at') if customer.company else Lead.objects.filter(
        customer_name__iexact=customer.name,
    ).order_by('-created_at')
    credit_assessments = CreditAssessment.objects.filter(customer=customer).select_related('requested_by').order_by('-created_at')
    return render(request, 'database/customer_detail.html', {
        'customer': customer,
        'leads': leads,
        'team_choices': Customer.TEAM_CHOICES,
        'credit_assessments': credit_assessments,
    })


@login_required
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added.')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'database/customer_add.html', {'form': form})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated.')
            return redirect('customer_detail', pk=pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'database/customer_edit.html', {'form': form, 'customer': customer})


@login_required
def customer_handover(request, pk):
    if request.user.role not in ('lead', 'admin'):
        messages.error(request, 'Only team leads and admins can reassign customers.')
        return redirect('customer_detail', pk=pk)
    if request.method != 'POST':
        return redirect('customer_detail', pk=pk)
    customer = get_object_or_404(Customer, pk=pk)
    team = request.POST.get('team', '')
    valid_teams = [t for t, _ in Customer.TEAM_CHOICES]
    if team in valid_teams:
        customer.handling_team = team
        customer.save(update_fields=['handling_team'])
        messages.success(request, f'{customer.name} handed over to {customer.get_handling_team_display()}.')
    elif team == '':
        customer.handling_team = ''
        customer.save(update_fields=['handling_team'])
        messages.success(request, f'{customer.name} unassigned from all teams.')
    return redirect('customer_detail', pk=pk)


@login_required
def broker_list(request):
    if request.user.team != 'market' and request.user.role != 'admin':
        return redirect('dashboard')
    scope = request.GET.get('scope', 'active')
    if scope == 'all':
        qs = Broker.objects.all()
    else:
        qs = Broker.objects.filter(is_active=True)
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'database/broker_list.html', {
        'brokers': page_obj.object_list,
        'page_obj': page_obj,
        'scope': scope,
    })


@login_required
def broker_create(request):
    if not (request.user.role in ('lead', 'admin') and
            (request.user.team == 'market' or request.user.role == 'admin')):
        return redirect('dashboard')
    if request.method == 'POST':
        form = BrokerForm(request.POST)
        if form.is_valid():
            broker = form.save()
            messages.success(request, f'Broker "{broker.name}" added.')
            return redirect('broker_list')
    else:
        form = BrokerForm()
    return render(request, 'database/broker_create.html', {'form': form})


@login_required
def broker_edit(request, pk):
    if not (request.user.role in ('lead', 'admin') and
            (request.user.team == 'market' or request.user.role == 'admin')):
        return redirect('dashboard')
    broker = get_object_or_404(Broker, pk=pk)
    if request.method == 'POST':
        form = BrokerForm(request.POST, instance=broker)
        if form.is_valid():
            form.save()
            messages.success(request, f'Broker "{broker.name}" updated.')
            return redirect('broker_list')
    else:
        form = BrokerForm(instance=broker)
    return render(request, 'database/broker_create.html', {'form': form, 'broker': broker})


@login_required
def broker_delete(request, pk):
    if not (request.user.role in ('lead', 'admin') and
            (request.user.team == 'market' or request.user.role == 'admin')):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('broker_list')
    broker = get_object_or_404(Broker, pk=pk)
    name = broker.name
    broker.delete()
    messages.success(request, f'Broker "{name}" deleted.')
    return redirect('broker_list')


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{product.product_name}" updated.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'database/product_edit.html', {'form': form, 'product': product})


@login_required
def product_delete(request, pk):
    if request.method != 'POST':
        return redirect('product_list')
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, f'"{product.product_name}" deleted.')
    return redirect('product_list')


@login_required
def product_hsn_lookup(request):
    """Return the HSN code for the first product matching the query (item_no/product_name)."""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'hsn_code': ''})
    product = Product.objects.filter(is_active=True).filter(
        Q(item_no__icontains=q) | Q(product_name__icontains=q)
    ).exclude(hsn_code='').first()
    return JsonResponse({'hsn_code': product.hsn_code if product else ''})
