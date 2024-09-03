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
from apps.home.models import VM
from apps.home.services.proxmox_service import get_proxmox_nodes, create_vm, get_vm_name_list, delete_vm, \
    run_ansible_playbook, remove_vm, start_vm, stop_proxmox_vm_function, take_snapshot, snapshot_list, editVM, \
    remove_snapshot_service, backupvm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
    output = vm_creation_result.get('output', '')
    logs=""

    print ("eye the logs in django",output)
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


def snapshot_vm(request):


   return  take_snapshot(request)



from django.shortcuts import redirect
from django.http import JsonResponse
def remove_snapshot_vm(request,vmid,snapshotName):

    if request.method == 'GET':

            # Example function to handle the snapshot
         remove_snapshot_service(vmid,snapshotName)
    return redirect(f'/vm/{vmid}/snapshots/')





def editVM_listview(request):
    return render(request, "home/update-vm-list.html")
@csrf_exempt
def backupvmView(request):
    backupvm(request)
    return redirect("/showvmbackup/")

    return render(request, "home/update-vm-list.html")
@csrf_exempt
def showvmbackup(request):
    return render(request, "home/backup-list.html")




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


@csrf_exempt
def editVMdisk_view(request, vmid, disk):
    if request.method == 'GET':
        try:
            # Call the editVM function and capture the result
            response = editVM(vmid, None, None, disk, None)
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

# views.py
from django.shortcuts import render
from django.http import JsonResponse
from proxmoxer import ProxmoxAPI
from django.conf import settings

def get_vm_snapshots(request, vmid):
    try:
        # Proxmox API connection
        proxmox = ProxmoxAPI('192.168.187.137', user='root@pam', password='00000', verify_ssl=False, port=8006)
        # Retrieve the snapshots of the specified VM
        snapshots = proxmox.nodes("proxmox").qemu(vmid).snapshot.get()

        # Render the snapshots in the template
        return render(request, 'home/vm_snapshots.html', {'snapshots': snapshots, 'vmid': vmid})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#
# def get_all_backups_view(request,storage,vmid):
#     get_all_backups(request,storage,vmid)
#     return render(request, 'layouts/base.html', )


def backups_list(request, vmid):
    api_url = 'https://192.168.187.137:8006/api2/json'
    login_url = f'{api_url}/access/ticket'
    api_user = 'root@pam'
    api_password = '00000'
    node = 'proxmox'  # Replace with your Proxmox node name
    storage = 'local'  # Replace with your storage name

    # Login and get ticket and CSRF token
    login_data = {
        'username': api_user,
        'password': api_password
    }

    try:
        # Perform login request
        login_response = requests.post(login_url, data=login_data, verify=False)
        login_response.raise_for_status()
        data = login_response.json()['data']
        ticket = data['ticket']
        csrf_token = data['CSRFPreventionToken']

        # Setup headers for authenticated requests
        headers = {
            'Authorization': f'PVEAuthCookie={ticket}',
            'CSRFPreventionToken': csrf_token
        }

        # Fetch backups from the storage
        backups_url = f'{api_url}/nodes/{node}/storage/{storage}/content'
        backups_response = requests.get(backups_url, headers=headers, verify=False)
        backups_response.raise_for_status()
        backups_data = backups_response.json()

        # Filter backups by VM ID
        if 'data' in backups_data:
            backups = [backup for backup in backups_data['data'] if backup.get('vmid') == int(vmid)]
        else:
            backups = []

        # Render HTML template with filtered backups data
        return render(request, 'home/backups_list.html', {'backups': backups, 'vmid': vmid})

    except requests.RequestException as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


@csrf_exempt
def restore(request):
    if request.method == 'POST':
        vmid = request.POST.get('vmid')

        print(f"VM ID: {vmid}")

        # Validate input
        if not vmid:
            return JsonResponse({'error': 'VM ID is required'}, status=400)

        # Path to your Ansible playbook
        playbook_path = '/home/hadil/workspace1/playbook_backup_create.yml'

        # Run the Ansible playbook
        result = subprocess.run(
            ['ansible-playbook',playbook_path,'-i', '/home/hadil/workspace1/inventory.ini', '--extra-vars', f'vmid={vmid} backup_mode={backup_mode} compress={compress} storage={storage} protect={protect} note={note}'],
            capture_output=True, text=True
        )
        print("me herererere")
        # Get the full output
        print("Playbook Output (stdout):")
        print(result.stdout)

        # To print the standard error
        print("Playbook Errors (stderr):")
        print(result.stderr)
        full_output = result.stdout + result.stderr
        if result.returncode == 0:
             JsonResponse({'status': 'success', 'output': full_output})
             return  redirect("/showvmbackup/")
        else:
            return JsonResponse({'status': 'error', 'output': full_output}, status=500)