import json

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from quotations.models import Lead
from .forms import BrokerForm, CustomerForm, ProductForm
from .models import Broker, Customer, Product


def _build_product_groups(products):
    groups = {}
    for p in products.order_by('sub_type', 'size', 'make', 'length', 'grade', 'site'):
        key = f"{p.sub_type}||{p.size}"
        if key not in groups:
            groups[key] = {
                'type_display': p.get_sub_type_display() or p.get_make_display(),
                'size': p.size,
                'makes': {},
            }
        g = groups[key]
        mk = p.make
        if mk not in g['makes']:
            g['makes'][mk] = {'display': p.get_make_display(), 'lengths': {}}
        lk = p.length or ''
        if lk not in g['makes'][mk]['lengths']:
            g['makes'][mk]['lengths'][lk] = {'grades': {}}
        gk = p.grade or ''
        if gk not in g['makes'][mk]['lengths'][lk]['grades']:
            g['makes'][mk]['lengths'][lk]['grades'][gk] = {'sites': {}}
        sk = p.site or ''
        g['makes'][mk]['lengths'][lk]['grades'][gk]['sites'][sk] = {
            'id': p.pk,
            'rate': str(p.rate),
            'qty': str(p.quantity),
            'hsn': p.hsn_code,
            'godown': p.godown or '',
            'site_display': p.get_site_display() if p.site else '',
            'pieces': p.pieces,
        }
    return groups


@login_required
def product_list(request):
    q = request.GET.get('q', '').strip()

    products = Product.objects.filter(is_active=True)

    if q:
        products = products.filter(
            Q(size__icontains=q) |
            Q(hsn_code__icontains=q) |
            Q(grade__icontains=q) |
            Q(godown__icontains=q)
        )

    groups = _build_product_groups(products)

    return render(request, 'database/product_list.html', {
        'groups_json': json.dumps(groups),
        'group_count': len(groups),
        'q': q,
    })


@login_required
def product_catalog_json(request):
    groups = _build_product_groups(Product.objects.filter(is_active=True))
    return JsonResponse(groups)


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
def customer_list(request):
    scope = request.GET.get('scope', 'team')
    if scope == 'all':
        customers = Customer.objects.all()
    elif request.user.role == 'admin':
        customers = Customer.objects.all()
    elif request.user.team:
        customers = Customer.objects.filter(handling_team=request.user.team)
    else:
        customers = Customer.objects.none()
    return render(request, 'database/customer_list.html', {
        'customers': customers,
        'scope': scope,
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
    return render(request, 'database/customer_detail.html', {
        'customer': customer,
        'leads': leads,
        'team_choices': Customer.TEAM_CHOICES,
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
        brokers = Broker.objects.all()
    else:
        brokers = Broker.objects.filter(is_active=True)
    return render(request, 'database/broker_list.html', {
        'brokers': brokers,
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
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{product.size}" updated.')
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
    messages.success(request, f'"{product.size}" deleted.')
    return redirect('product_list')


@login_required
def product_hsn_lookup(request):
    """Return the HSN code for the first product matching the query (size or sub_type)."""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'hsn_code': ''})
    product = Product.objects.filter(is_active=True).filter(
        Q(size__icontains=q) | Q(sub_type__icontains=q)
    ).exclude(hsn_code='').first()
    return JsonResponse({'hsn_code': product.hsn_code if product else ''})
