# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views
from apps.home.views import get_proxmox_nodes_view, create_proxmox_vm, vm_names, base_view, edit_proxmox_vm, list_vms, \
    removeVm, removeVmlist, start_proxmox_vm

#from apps.home.views import get_proxmox_nodes_view, create_proxmox_vm
urlpatterns = [
    path('proxmox/nodes/', get_proxmox_nodes_view, name='proxmox_nodes'),
    path('create-vm/', create_proxmox_vm, name='create_vm'),
    path('start-vm/<int:vmid>/', start_proxmox_vm, name='start_proxmox_vm'),
   # path('stop-vm/<int:vmid>/', stop_proxmox_vm, name='stop_proxmox_vm'),
    path('delete-vm/<int:vmid>/', removeVm, name='remove_vm'),
    path('delete-list/', removeVmlist, name='remove-vm-list'),
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
    path('', base_view, name='base_view'),
   #path('', views.index, name='home'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
