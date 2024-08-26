# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import requests
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.template import loader
from django.urls import reverse
from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.home.models import VM
from apps.home.services.proxmox_service import get_proxmox_nodes, create_vm, get_vm_name_list, delete_vm, \
    run_ansible_playbook, remove_vm, start_vm, stop_proxmox_vm_function, take_snapshot, snapshot_list, editVM


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


def index_home1(request):
    return render(request, 'home/index.html')


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


def get_proxmox_nodes_view(request):
    try:
        node_list = get_proxmox_nodes()
        return JsonResponse({"nodes": node_list})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def create_proxmox_vm(request):
    vm_creation_result = create_vm(request)
    vms_data = get_vm_name_list()

    # Extract status, message, and logs from the result
    status = vm_creation_result.get('status')
    msg = vm_creation_result.get('msg', '')
    logs = vm_creation_result.get('logs', '')

    return render(request, 'home/create-vm.html', {
        'vms_data': vms_data,
        'status': status,
        'msg': msg,
        'logs': logs
    })

def start_proxmox_vm(request,vmid):
    start_vm(request,vmid)
    return  render (request,"home/vm_info.html",{'vmid': vmid})


def stop_proxmox_vm(request,vmid):
    stop_proxmox_vm_function(request,vmid)
    return render(request, "home/vm_info.html", {'vmid': vmid})








def edit_proxmox_vm(request):
    vms_data = get_vm_name_list()
    return  render (request,"home/edit-vm.html",{'vms_data': vms_data})
def list_vms (request):
    vms_data = get_vm_name_list()
    return  render (request,"home/vm-list.html",{'vms_data': vms_data})


def d(request):
    vms_data=get_vm_name_list()
    print("look here",vms_data)
    return render(request,'home/dashboard.html')


def vm_names(request):
    vms_data=get_vm_name_list()
   # print("look here",vms_data)
    return render(request,'home/dashboard.html',{'vms_data': vms_data})
def stream_ansible_logs(request):
    stream_ansible_logs(request)





# render views #

#def dashboard_view(request):
 #   return render(request, 'home/dashboard.html')


def vmInfo(request,vmid):
    vminfo = VM()
    vms_data = get_vm_name_list()  # Retrieve VM names and states for the sidebar
    for vm in vms_data:
        if vmid == vm['vmid']:
            vminfo=vm
            print("here the vminfo",vminfo)
            break
        if vminfo is None:
            return HttpResponseNotFound("<h1>VM Not Found</h1>")

    return render(request,'home/vm_info.html',{'vms_data': vms_data,'vminfo':vminfo,'vmid':vmid})

def removeVm(request,vmid):
    remove_vm(request,vmid)
    return render(request,'home/delete-vm-list.html')
def removeVm_in_info_vm(request,vmid):
    remove_vm(request,vmid)
    return  render(request,"home/vm-list.html",{'vmid':vmid})


def snapshot_vm(request,vmid,name,description):
    print(vmid,name,description)
    if request.method == 'GET':
        try:
            # Example function to handle the snapshot
            take_snapshot(vmid, name, description)

            return render(request, "home/snapshot-list.html", {'vmid': vmid})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)



def editVM_listview(request):
    return render(request, "home/update-vm-list.html")


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def editVM_view(request, vmid, memory=None, processors=None, disk=None, isoimage=None):
    if request.method == 'GET':
        try:
            # Call the editVM function and capture the result
            response = editVM(vmid, memory, processors, disk, isoimage)
            print("Playbook Output:\n", response['output'])  # Print the playbook output to the terminal
            print("Playbook Errors:\n", response['errors'])  # Print any errors to the terminal

            return render(request, "home/update-vm-list.html")
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)

@csrf_exempt
def editVMprocessors_view(request, vmid, processors):
    if request.method == 'GET':
        try:
            # Call the editVM function and capture the result
            response = editVM(vmid, None, processors, None, None)
            print("Playbook Output:\n", response['output'])  # Print the playbook output to the terminal
            print("Playbook Errors:\n", response['errors'])  # Print any errors to the terminal

            return render(request, "home/update-vm-list.html")
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)






def snapshot_list_of_one_vm(request, vmid):
    snapshots= snapshot_list(request, vmid)
    return render(request, 'home/snapshot-info.html', {'snapshots': snapshots})


def snapshotlist(request):
    vms_data = get_vm_name_list()
    return render(request, 'home/snapshot-list.html',{'vms_data':vms_data})

def removeVmlist(request):
    vms_data = get_vm_name_list()

    return render(request,'home/delete-vm-list.html',{'vms_data':vms_data})






def base_view(request):
    vms_data = get_vm_name_list()  # Retrieve VM names and states for the sidebar
    return render(request, 'layouts/base.html', {'vms_data': vms_data})

