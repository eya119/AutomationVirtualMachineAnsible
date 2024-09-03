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
        # Convert the Ansible Runner output to a string for HTML rendering
        stdout_output = '\n'.join(result.stdout.readlines())
        print ("jjjjjj",stdout_output)
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

                return JsonResponse({'status': 'success', 'rc': result.rc,'output': stdout_output})
            except (KeyError, IndexError):
                return JsonResponse({'status': 'failed', 'msg': 'Error parsing VM IP address','rc': result.rc,'output': stdout_output})
        else:
            return JsonResponse({'status': 'failed', 'msg': 'Ansible playbook failed', 'rc': result.rc,'output': stdout_output})

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

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def snapshot_vm(request, vmid, name, description):
    if request.method == 'GET':
        try:
            # Call the snapshot function with the provided arguments
            take_snapshot(vmid, name, description)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'failed', 'message': 'Invalid request'}, status=400)



def take_snapshot(request):
    if request.method == 'POST':
        vmid = request.POST.get('vmid')
        name = request.POST.get('name')
        description = request.POST.get('description')

        # Path to your Ansible playbook
        playbook_path = '/home/hadil/workspace1/playbook_snapshot_vm.yml'

        # Run the Ansible playbook with additional variables
        result = subprocess.run(
            [
                'ansible-playbook', playbook_path,
                '--extra-vars', f'vmid={vmid} snapshot_name={name} description="{description}"'
            ],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            # Render the HTML template with any context you need
            html_content = render(request, "home/snapshot-list.html").content.decode('utf-8')
            return JsonResponse({'status': 'success', 'html': html_content})
        else:
            return JsonResponse({'status': 'error', 'message': result.stderr}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

from django.shortcuts import redirect

@csrf_exempt
def remove_snapshot_service(vmid,snapshotName):
    try:
        if not vmid:
            return JsonResponse({'status': 'error', 'message': 'VM ID not provided'}, status=400)

        # Path to your Ansible playbook
        playbook_path = '/home/hadil/workspace1/playbook_delete_snapshot.yml'

        # Run the Ansible playbook with additional variables
        result = subprocess.run(
            [
                'ansible-playbook', playbook_path,
                '--extra-vars', f'vmid={vmid} snapshot_name={snapshotName}'
            ],
            capture_output=True, text=True
        )

        # Log the command and result for debugging
        print(f"Executed command: ansible-playbook {playbook_path} --extra-vars vmid={vmid}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")

        # Check if the playbook run was successful
        if result.returncode == 0:
            return  redirect('/vm/100/snapshots/')
        else:
            return JsonResponse({'status': 'error', 'message': result.stderr}, status=500)

    except Exception as e:
        # Log the exception for debugging
        print(f"Exception occurred: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


import subprocess

import subprocess

def editVM(vmid, memory=None, processors=None, disk=None, isoimage=None):
    try:
        if not vmid:
            return {'status': 'error', 'message': 'VM ID not provided'}

        # Base extra_vars string
        extra_vars_base = f"vmid={vmid}"

        # Initialize result variables
        result = None

        # Prepare and run the Ansible playbooks
        if memory:
            extra_vars = f"{extra_vars_base} vm_memory={memory}"
            result = subprocess.run(
                ['ansible-playbook', '/home/hadil/workspace1/playbook_upload_memory.yml', '--extra-vars', extra_vars],
                capture_output=True, text=True
            )
        if processors:
            extra_vars = f"{extra_vars_base} vm_cores={processors}"
            result = subprocess.run(
                ['ansible-playbook', '/home/hadil/workspace1/playbook_upload_processors.yml', '--extra-vars', extra_vars],
                capture_output=True, text=True
            )
        if disk:
            extra_vars = f"{extra_vars_base} size={disk}G"
            result = subprocess.run(
                ['ansible-playbook', '/home/hadil/workspace1/playbook_upload_disk.yml','-i', '/home/hadil/workspace1/inventory.ini',  '--extra-vars', extra_vars],
                capture_output=True, text=True
            )
        if isoimage:
            extra_vars = f"{extra_vars_base} iso_image={isoimage}"
            result = subprocess.run(
                ['ansible-playbook', '/home/hadil/workspace1/playbook_upload_iso.yml', '--extra-vars', extra_vars],
                capture_output=True, text=True
            )

        # Check if any playbook was executed
        if not result:
            return {'status': 'error', 'message': 'No changes were made', 'output': '', 'errors': ''}

        # Capture and return the playbook output and errors
        output = result.stdout
        errors = result.stderr

        # Check if the playbook run was successful
        if result.returncode == 0:
            return {'status': 'success', 'message': 'VM edited successfully', 'output': output, 'errors': errors}
        else:
            return {'status': 'error', 'message': errors, 'output': output, 'errors': errors}

    except Exception as e:
        return {'status': 'error', 'message': str(e), 'output': '', 'errors': ''}






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





def snapshot_list(request, vmid):
    # Proxmox API details
    api_url = 'https://your-proxmox-url:8006/api2/json'
    login_url = f'{api_url}/access/ticket'
    api_user = 'root@pam'
    api_password = '00000'

    # Login and get ticket and CSRF token
    login_data = {
        'username': api_user,
        'password': api_password
    }

    try:
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

        # Fetch snapshots for the VM
        snapshots_url = f'{api_url}/nodes/proxmox/qemu/{vmid}/snapshot'
        snapshots_response = requests.get(snapshots_url, headers=headers, verify=False)
        snapshots_response.raise_for_status()
        snapshots_data = snapshots_response.json()['data']

        # Prepare data for rendering
        snapshot_list = []
        for snapshot in snapshots_data:
            snapshot_list.append({
                'name': snapshot.get('name'),
                'description': snapshot.get('description', ''),
                'date': snapshot.get('creation')
            })

        return render(request, 'home/snapshot-info.html', {'snapshots': snapshot_list})

    except requests.RequestException as e:
        return JsonResponse({'status': 'failed', 'message': str(e)}, status=500)
@csrf_exempt
def backupvm(request):
    if request.method == 'POST':
        vmid = request.POST.get('vmid')
        backup_mode = request.POST.get('mode')
        compress = request.POST.get('compression')
        storage = request.POST.get('storage')
        protect = request.POST.get('protect')
        note = request.POST.get('note')

        print(f"VM ID: {vmid}")
        print(f"Backup Mode: {backup_mode}")
        print(f"Compression: {compress}")
        print(f"Storage: {storage}")
        print(f"Protect: {protect}")
        print(f"Note: {note}")

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















