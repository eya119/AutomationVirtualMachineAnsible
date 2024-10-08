# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views
from apps.home.services.proxmox_service import editVM
from apps.home.views import get_proxmox_nodes_view, create_proxmox_vm, vm_names, base_view, edit_proxmox_vm, list_vms, \
    removeVm, removeVmlist, start_proxmox_vm, stop_proxmox_vm, removeVm_in_info_vm, snapshot_vm, snapshotlist, \
    snapshot_list_of_one_vm, editVM_listview, editVM_view, editVMprocessors_view, editVMdisk_view, get_vm_snapshots, \
    remove_snapshot_vm, showvmbackup, backupvmView, backups_list, restore, restorelist, id_backups_list, \
    allthe_backups_list, removebackup, index_home2

#from apps.home.views import get_proxmox_nodes_view, create_proxmox_vm
urlpatterns = [
    path('proxmox/nodes/', get_proxmox_nodes_view, name='proxmox_nodes'),
    path('create-vm/', create_proxmox_vm, name='create_vm'),
    path('update-vm-memory/<int:vmid>/<int:memory>/', editVM_view, name='update-vm-memory'),
    path('update-vm-disk/<int:vmid>/<int:disk>/', editVMdisk_view, name='update-vm-disk'),
    path('update-vm-iso/<int:vmid>/<int:iso>/', editVM_view, name='update-vm-iso'),
    path('update-vm-processors/<int:vmid>/<str:processors>/', editVMprocessors_view, name='update-vm-processors'),
    path('editVMlist/', editVM_listview, name='editVMlist'),
    path('vm/<int:vmid>/snapshots/', get_vm_snapshots, name='get_vm_snapshots'),
    path('start-vm/<int:vmid>/', start_proxmox_vm, name='start_proxmox_vm'),
    path('remove-vm-snapshot/<int:vmid>/<str:snapshotName>/', remove_snapshot_vm, name='remove-vm-snapshot'),
    path('stop-vm/<int:vmid>/', stop_proxmox_vm, name='stop_proxmox_vm'),
    path('snapshot-list/', snapshotlist, name='snapshot-list'),
    path('showvmbackup/', showvmbackup, name='showvmbackup'),
    path('createbackup/', backupvmView, name='createbackup'),
    path('list-backups/<int:vmid>/', backups_list, name='list_backups'),
    path('allthe_backups_list/', allthe_backups_list, name='allthe_backups_list'),
    re_path(r'^restore/(?P<vmid>\d+)/(?P<backup_file>.+)/$', restore, name='restore'),
    re_path(r'^removebackup/(?P<backup_file>.+)/$', removebackup, name='removebackup'),




    path('snapshot/', snapshot_vm, name='snapshot_vm'),
    path('restorelist/', id_backups_list, name='restorelist'),
    path('snapshotvmlist/<int:vmid>/', snapshot_list_of_one_vm, name='snapshot_list_of_one_vm'),
    path('delete-vm-machine/<int:vmid>/', removeVm_in_info_vm, name='removeVm_in_info_vm'),
    path('delete-vm/<int:vmid>/', removeVm, name='remove_vm'),
    path('backup-list/', removeVmlist, name='remove-vm-list'),
    path('edit-vm/', edit_proxmox_vm, name='edit_vm'),
    path('list-vms/', list_vms, name='list_vms'),
    path('stream-logs/', views.stream_ansible_logs, name='stream_ansible_logs'),


    # html pages
    path('dashboard/',views.vm_names,name='dashboard_view'),
    path('sidebar/',views.vm_names,name='sidebar-view'),
    path('vm-info/<int:vmid>/',views.vmInfo,name='vm_info'),

  #  path('vms/delete/<int:vmid>/', views.delete_vm_view, name='delete_vm'),
    #path('delete-vm/<str:node>/<int:vmid>/', views.delete_vm_view, name='delete_vm'),
    # The home page
    #path('', base_view, name='base_view'),


   path('', index_home2, name='home'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
