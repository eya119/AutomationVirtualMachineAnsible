import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from proxmoxer import ProxmoxAPI
from django.conf import settings


class VMDetailConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.channel_layer = self.channel_layer
        self.vm_id = None
        self.fetch_status_task = None

        # Start periodic task if a VM ID is provided in the initial connection
        if self.vm_id:
            self.fetch_status_task = asyncio.create_task(self.periodic_status_fetch())

    async def disconnect(self, close_code):
        if self.fetch_status_task:
            self.fetch_status_task.cancel()
            try:
                await self.fetch_status_task
            except asyncio.CancelledError:
                pass

    async def receive(self, text_data=None):
        if text_data:
            data = json.loads(text_data)
            if 'vmid' in data:
                self.vm_id = data['vmid']
                # If there's an existing task, cancel it and start a new one
                if self.fetch_status_task:
                    self.fetch_status_task.cancel()
                    try:
                        await self.fetch_status_task
                    except asyncio.CancelledError:
                        pass
                self.fetch_status_task = asyncio.create_task(self.periodic_status_fetch())

    async def periodic_status_fetch(self):
        while True:
            if self.vm_id:
                status = await self.get_vm_status_by_id(self.vm_id)
                await self.send(text_data=json.dumps(status))
            await asyncio.sleep(6)  # Wait for 10 seconds before fetching again

    async def get_vm_status_by_id(self, vmid):
        proxmox_server = settings.PROXMOX_SETTINGS['api_host']
        username = settings.PROXMOX_SETTINGS['username']
        password = settings.PROXMOX_SETTINGS['password']
        realm = settings.PROXMOX_SETTINGS['realm']

        if proxmox_server.startswith('https://'):
            proxmox_server = proxmox_server[len('https://'):]

        try:
            proxmox = ProxmoxAPI(proxmox_server, user=f"{username}@{realm}", password=password, verify_ssl=False)
            vm_status = proxmox.nodes('proxmox').qemu(vmid).status.current.get()

            # Convert memory and disk sizes from bytes to GB
            memory_mb = vm_status.get('mem', 0) / 1024
            max_disk_gb = vm_status.get('maxdisk', 0) / (1024 ** 3)

            return {
                'vmid': vmid,
                'name': vm_status.get('name', 'N/A'),
                'status': vm_status.get('status', 'N/A'),
                'cpu': f"{vm_status.get('cpu', 'N/A')}%",
                'mem': f"{memory_mb:.2f} MB",
                'disk': f"{vm_status.get('disk', 'N/A')} GB",
                'maxdisk': f"{max_disk_gb:.2f} GB"
            }
        except Exception as e:
            return {'error': f"Failed to fetch VM status for VM ID {vmid}: {str(e)}"}


class VMListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.channel_layer = self.channel_layer
        await self.send_all_vms_status()

    async def disconnect(self, close_code):
        pass

    async def send_all_vms_status(self):
        status_list = await self.get_all_vms_status()
        await self.send(text_data=json.dumps(status_list))
        self.status_update_task = asyncio.create_task(self.send_periodic_all_vms_updates())

    async def send_periodic_all_vms_updates(self):
        while True:
            status_list = await self.get_all_vms_status()
            await self.send(text_data=json.dumps(status_list))
            await asyncio.sleep(10)

    async def get_all_vms_status(self):
        proxmox_server = settings.PROXMOX_SETTINGS['api_host']
        username = settings.PROXMOX_SETTINGS['username']
        password = settings.PROXMOX_SETTINGS['password']
        realm = settings.PROXMOX_SETTINGS['realm']

        if proxmox_server.startswith('https://'):
            proxmox_server = proxmox_server[len('https://'):]

        try:
            proxmox = ProxmoxAPI(proxmox_server, user=f"{username}@{realm}", password=password, verify_ssl=False)
            vms = proxmox.nodes('proxmox').qemu.get()
            print(json.dumps(vms, indent=10))

            status_list = []
            for vm in vms:
                vmid = vm.get('vmid')
                vm_status = await self.get_vm_status_by_id(vmid)
                status_list.append(vm_status)

            return status_list
        except Exception as e:
            return {'error': f"Failed to fetch VMs status: {str(e)}"}

    async def get_vm_status_by_id(self, vmid):
        proxmox_server = settings.PROXMOX_SETTINGS['api_host']
        username = settings.PROXMOX_SETTINGS['username']
        password = settings.PROXMOX_SETTINGS['password']
        realm = settings.PROXMOX_SETTINGS['realm']

        if proxmox_server.startswith('https://'):
            proxmox_server = proxmox_server[len('https://'):]

        try:
            proxmox = ProxmoxAPI(proxmox_server, user=f"{username}@{realm}", password=password, verify_ssl=False)
            vm_status = proxmox.nodes('proxmox').qemu(vmid).status.current.get()

            return {
                'vmid': vmid,
                'name': vm_status.get('name', 'N/A'),
                'status': vm_status.get('status', 'N/A'),
                'cpu': f"{vm_status.get('cpu', 'N/A')*100:.2f}%",
                'cpunumb': f"{vm_status.get('cpus', 'N/A') }",
                #'mem': f"{vm_status.get('mem', 'N/A')}MB",
                'mem': f"{(vm_status.get('mem', 0) / vm_status.get('maxmem', 1)) * 100:.2f}%",
                'uptime': f"{vm_status.get('uptime', 0) // 3600}:h {(vm_status.get('uptime', 0) % 3600) // 60}:m {vm_status.get('uptime', 0) % 60}:s",

                # Calculate memory usage as a percentage

                'disk': f"{vm_status.get('disk', 'N/A')}GB"
            }
        except Exception as e:
            return {'error': f"Failed to fetch VM status for VM ID {vmid}: {str(e)}"}
