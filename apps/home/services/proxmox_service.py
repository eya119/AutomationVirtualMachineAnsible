import os
import subprocess
import warnings

from django.conf import settings
from keystoneauth1.http_basic import HTTPBasicAuth
from neutron.ipam import requests
from proxmoxer import ProxmoxAPI
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import ansible_runner
from django.shortcuts import render
from requests import RequestException
from urllib3.exceptions import InsecureRequestWarning

from apps.home.models import VM
import requests
import json  # Import the json module
from subprocess import run, PIPE

api_user = settings.PROXMOX_SETTINGS['api_user']
api_password = settings.PROXMOX_SETTINGS['password']
node = 'proxmox'

def get_proxmox_nodes():
    proxmox_server = settings.PROXMOX_SETTINGS['server']
    username = settings.PROXMOX_SETTINGS['username']
    password = settings.PROXMOX_SETTINGS['password']
    realm = settings.PROXMOX_SETTINGS['realm']

    try:
        #connect to proxmox API
        proxmox = ProxmoxAPI(proxmox_server, user=f"{username}@{realm}", password=password, verify_ssl=False)
        # retruve nodes
        nodes = proxmox.nodes.get()
        node_list = [{"name": node["node"], "status": node["status"]} for node in nodes]
        print(node_list)

        return node_list
    except Exception as e:
        print('Failed to retrieve Proxmox nodes')
        raise Exception(f"Failed to retrieve Proxmox nodes: {e}")


@csrf_exempt
def create_vm(request):
    if request.method == 'POST':
        # Extract data from the POST request
        api_host = request.POST.get('api_host')
        api_user = request.POST.get('api_user')
        api_password = request.POST.get('api_password')
        vm_name = request.POST.get('vm_name')
        node = request.POST.get('node')
        vmid = request.POST.get('vmid')
        vm_memory = request.POST.get('vm_memory')
        vm_cores = request.POST.get('vm_cores')
        vm_disk = request.POST.get('vm_disk')
        vm_bridge = request.POST.get('vm_bridge')
        iso_image = request.POST.get('iso_image')
        ostype = request.POST.get('ostype')
        cpu = request.POST.get('cpu')
        vm_balloon = request.POST.get('vm_balloon') or 1024  # Default to 1024 if not provided

        # For debugging
        print(f"Debug: api_host: {api_host}, api_user: {api_user}, vm_name: {vm_name}")

        # Defining the path of the playbook and roles
        playbook_path = os.path.join('/home/hadil/workspace1', 'playbook_create_vm.yml')
        roles_path = os.path.join('/home/hadil/workspace1', 'roles')

        # Defining extra variables to pass to the playbook
        extravars = {
            'api_host': api_host,
            'api_user': api_user,
            'api_password': api_password,
            'vm_name': vm_name,
            'node': node,
            'vmid': vmid,
            'vm_memory': vm_memory,
            'vm_cores': vm_cores,
            'vm_disk': vm_disk,
            'vm_bridge': vm_bridge,
            'iso_image': iso_image,
            'ostype': ostype,
            'cpu': cpu,
            'vm_balloon': vm_balloon
        }

        # Running the Ansible playbook
        result = ansible_runner.run(
            playbook=playbook_path,
            roles_path=roles_path,
            extravars=extravars
        )

        # Checking the result of the playbook run
        if result.rc == 0:
            try:
                # Parse the JSON response to get the IP address
                vm_ip = None
                if 'events' in result and result['events']:
                    for event in result['events']:
                        if 'stdout' in event:
                            # Extract the JSON output from the Ansible task that registered the IP address
                            output = event['stdout']
                            if output:
                                try:
                                    data = json.loads(output)
                                    vm_ip = data.get('result', [])[0].get('ip-addresses', [])[0].get('ip-address')
                                    break
                                except (json.JSONDecodeError, IndexError, KeyError) as e:
                                    print(f"Error parsing IP from output: {e}")

                # Create and save the VM object in the database
                vm = VM(
                    name=vm_name,
                    ip_address=vm_ip,
                    node=node,
                    vmid=vmid,
                    memory=vm_memory,
                    cores=vm_cores,
                    disk=vm_disk,
                    bridge=vm_bridge,
                    cpu=cpu,
                    ostype=ostype
                )
                vm.save()

                return JsonResponse({'status': 'success', 'vm_ip': vm_ip})
            except (KeyError, IndexError):
                return JsonResponse({'status': 'failed', 'msg': 'Error parsing VM IP address'})
        else:
            return JsonResponse({'status': 'failed', 'msg': 'Ansible playbook failed', 'rc': result.rc})

    return JsonResponse({'status': 'failed', 'msg': 'Invalid request method'})


def get_vms(request):
    api_host = settings.PROXMOX_SETTINGS['api_host']
    # API URL to get VM details
    url = f"{api_host}/api2/json/nodes/{node}/qemu"

    try:
        # Make the API request to Proxmox
        response = requests.get(url, auth=HTTPBasicAuth(api_user, api_password), verify=False)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the JSON response
        data = response.json()
        vms = data.get('data', [])

        return render(request, 'vms_table.html', {'vms': vms})

    except requests.exceptions.RequestException as e:
        # Handle any request exceptions
        return JsonResponse({'error': str(e)})


def get_vm_name_list():
    # Define the URL for login and retrieving VM information
    login_url = f"https://192.168.187.137:8006/api2/json/access/ticket"
    login_data = {
        'username': api_user,
        'password': api_password
    }

    try:
        # Make the POST request to login
        login_response = requests.post(login_url, data=login_data, verify=False)
        login_response.raise_for_status()

        # Extract the ticket and CSRF token from the response
        data = login_response.json()['data']
        ticket = data['ticket']
        csrf_token = data['CSRFPreventionToken']

        # Set up headers for subsequent requests
        headers = {
            'Authorization': f'PVEAuthCookie={ticket}',
            'CSRFPreventionToken': csrf_token
        }

        # Define the URL to retrieve node information
        url = f"https://192.168.187.137:8006/api2/json/nodes"
        response = requests.get(url, cookies={'PVEAuthCookie': ticket}, headers=headers, verify=False)
        response.raise_for_status()

        nodes = response.json()['data']
        vms_data = []

        # Iterate over each node to get VMs
        for node in nodes:
            node_name = node['node']
            vm_url = f"https://192.168.187.137:8006/api2/json/nodes/{node_name}/qemu"
            vm_response = requests.get(vm_url, cookies={'PVEAuthCookie': ticket}, headers=headers, verify=False)

            if vm_response.status_code == 200:
                vms = vm_response.json()['data']
                for vm in vms:
                    vm_name = vm['name']
                    vmid = vm['vmid']
                    vm_state = vm.get('status', 'unknown')
                    vms_data.append({'name': vm_name, 'state': vm_state,'vmid':vmid})
                    #vm_names.append(vm['name'])
            else:
                print(f"Failed to retrieve VMs from node {node_name}. Status code: {vm_response.status_code}")

    except RequestException as e:
        print(f"An error occurred: {e}")
        return []

    return vms_data








def run_ansible_playbook(playbook_path, extravars):
    r = ansible_runner.run(
        playbook=playbook_path,
        extravars=extravars,
    )

    # Streaming logs
    for event in r.events:
        # Serialize event to JSON format
        yield json.dumps(event) + "\n"

    # Final status
    yield json.dumps({'status': r.status, 'rc': r.rc}) + "\n"
@csrf_exempt
def stream_ansible_logs(request):
    # Define playbook path and extra variables from POST request
    playbook_path = os.path.join('/home/hadil/workspace1', 'playbook_create_vm.yml')
    extravars = {
        'api_host': request.POST.get('host'),
        'api_user': request.POST.get('user'),
        'api_password': request.POST.get('password'),
        'vm_name': request.POST.get('vm_name'),
        'node': request.POST.get('node'),
        'vmid': request.POST.get('vmid'),
        'vm_memory': request.POST.get('vm_memory'),
        'vm_cores': request.POST.get('vm_cores'),
        'vm_disk': request.POST.get('vm_disk'),
        'vm_bridge': request.POST.get('vm_bridge'),
        'iso_image': request.POST.get('iso_image'),
        'ostype': request.POST.get('ostype'),
        'cpu': request.POST.get('cpu'),
    }

    # Function to generate the response stream
    def event_stream():
        for log in run_ansible_playbook(playbook_path, extravars):
            yield f"data: {log}\n\n"

    # StreamingHttpResponse with content type 'text/event-stream'
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


# Suppress only the single InsecureRequestWarning from urllib3 needed
warnings.simplefilter('ignore', InsecureRequestWarning)


import os
import ansible_runner
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
def delete_vm(request):
    # Extract data from the POST request
    api_host = request.POST.get('api_host')
    api_user = request.POST.get('api_user')
    api_password = request.POST.get('api_password')
    vmid = request.POST.get('vmid')

    # For debugging
    print(f"Debug: api_host: {api_host}, api_user: {api_user}, vmid: {vmid}")

    # Defining the path of the playbook and roles
    playbook_path = os.path.join('/home/hadil/workspace1', 'playbook_delete_vm.yml')
    roles_path = os.path.join('/home/hadil/workspace1', 'roles')

    # Defining extra variables to pass to the playbook
    extravars = {
        'api_host': api_host,
        'api_user': api_user,
        'api_password': api_password,
        'vmid': vmid
    }

    # Running the Ansible playbook
    result = ansible_runner.run(
        playbook=playbook_path,
        roles_path=roles_path,
        extravars=extravars
    )

    # Checking the result of the playbook run
    if result.rc == 0:
        try:
            # If successful, you might want to perform additional cleanup or logging
            return JsonResponse({'status': 'success', 'msg': f'VM with ID {vmid} has been deleted'})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'msg': f'Error occurred: {str(e)}'})
    else:
        return JsonResponse({'status': 'failed', 'msg': 'Ansible playbook failed', 'rc': result.rc})


@require_POST
def delete_vm(request):
    # Extract data from the POST request
    api_host = request.POST.get('api_host')
    api_user = request.POST.get('api_user')
    api_password = request.POST.get('api_password')
    vmid = request.POST.get('vmid')

    # For debugging
    print(f"Debug: api_host: {api_host}, api_user: {api_user}, vmid: {vmid}")

    # Defining the path of the playbook and roles
    playbook_path = os.path.join('/home/hadil/workspace1', 'playbook_delete_vm.yml')
    roles_path = os.path.join('/home/hadil/workspace1', 'roles')

    # Defining extra variables to pass to the playbook
    extravars = {
        'api_host': api_host,
        'api_user': api_user,
        'api_password': api_password,
        'vmid': vmid
    }

    # Running the Ansible playbook
    result = ansible_runner.run(
        playbook=playbook_path,
        roles_path=roles_path,
        extravars=extravars
    )

    # Checking the result of the playbook run
    if result.rc == 0:
        try:
            # If successful, you might want to perform additional cleanup or logging
            return JsonResponse({'status': 'success', 'msg': f'VM with ID {vmid} has been deleted'})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'msg': f'Error occurred: {str(e)}'})
    else:
        return JsonResponse({'status': 'failed', 'msg': 'Ansible playbook failed', 'rc': result.rc})


def run_ansible_playbook():
    try:
        playbook_path = os.path.join('/home/hadil/workspace1', 'playbook_create_vm.yml')
        result = subprocess.run(

            ['ansible-playbook', playbook_path],
            capture_output=True, text=True
        )
        return result.stdout  # Return playbook output
    except subprocess.CalledProcessError as e:
        return e.output  # Handle errors


@csrf_exempt
def remove_vm(request,vmid):
    try:

        if not vmid:
            return JsonResponse({'status': 'error', 'message': 'VM ID not provided'}, status=400)

        # Path to your Ansible playbook
        playbook_path = '/home/hadil/workspace1/playbook_delete_vm.yml'

        # Run the Ansible playbook
        result = subprocess.run(
            ['ansible-playbook', playbook_path, '--extra-vars', f'vmid={vmid}'],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            return JsonResponse({'status': 'success', 'output': result.stdout})
        else:
            return JsonResponse({'status': 'error', 'output': result.stderr}, status=500)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def start_vm(request,vmid):

    try:

        if not vmid:
            return JsonResponse({'status': 'error', 'message': 'VM ID not provided'}, status=400)

        # Path to your Ansible playbook
        playbook_path = '/home/hadil/workspace1/playbook_start_vm.yml'

        # Run the Ansible playbook
        result = subprocess.run(
            ['ansible-playbook', playbook_path, '--extra-vars', f'vmid={vmid}'],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            return JsonResponse({'status': 'success', 'output': result.stdout})
        else:
            return JsonResponse({'status': 'error', 'output': result.stderr}, status=500)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)@csrf_exempt



def stop_proxmox_vm_function(request,vmid):

    try:

        if not vmid:
            return JsonResponse({'status': 'error', 'message': 'VM ID not provided'}, status=400)

        # Path to your Ansible playbook
        playbook_path = '/home/hadil/workspace1/playbook_stop_vm.yml'

        # Run the Ansible playbook
        result = subprocess.run(
            ['ansible-playbook', playbook_path, '--extra-vars', f'vmid={vmid}'],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            return JsonResponse({'status': 'success', 'output': result.stdout})
        else:
            return JsonResponse({'status': 'error', 'output': result.stderr}, status=500)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
