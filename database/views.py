from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from quotations.models import Lead
from .forms import BrokerForm, CustomerForm, ProductForm
from .models import Broker, Customer, Product


@login_required
def product_list(request):
    type_filter = request.GET.get('type', '')
    sub_type_filter = request.GET.get('sub_type', '')
    q = request.GET.get('q', '').strip()

    products = Product.objects.filter(is_active=True)

    if type_filter in ('main', 'rolling', 'plate'):
        products = products.filter(type=type_filter)

    valid_sub_types = [k for k, _ in Product.SUB_TYPE_CHOICES]
    if sub_type_filter in valid_sub_types:
        products = products.filter(sub_type=sub_type_filter)

    if q:
        products = products.filter(
            Q(size__icontains=q) |
            Q(hsn_code__icontains=q) |
            Q(grade__icontains=q) |
            Q(location__icontains=q)
        )

    return render(request, 'database/product_list.html', {
        'products': products,
        'type_filter': type_filter,
        'sub_type_filter': sub_type_filter,
        'q': q,
        'sub_type_choices': Product.SUB_TYPE_CHOICES,
    })


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
    scope = request.GET.get('scope', '')
    if request.user.role == 'admin' and scope == 'all':
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
def broker_list(request):
    if request.user.team != 'market' and request.user.role != 'admin':
        return redirect('dashboard')
    brokers = Broker.objects.all()
    return render(request, 'database/broker_list.html', {'brokers': brokers})


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
