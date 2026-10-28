

# -*- mode: ruby -*-
# vi: set ft=ruby :

# Practica 1 - Infraestructura Big Data
# nodo1: Master
# nodo2: Worker 1
# nodo3: Worker 2

CAJA = "bento/ubuntu-24.04"

NODOS = [
  { nombre: "nodo1", ip: "192.168.56.10" },
  { nombre: "nodo2", ip: "192.168.56.11" },
  { nombre: "nodo3", ip: "192.168.56.12" },
]

Vagrant.configure("2") do |config|
  config.vm.box = CAJA
  config.vm.synced_folder ".", "/vagrant", disabled: true

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 2048
    vb.cpus = 2
  end

  NODOS.each do |n|
    config.vm.define n[:nombre] do |nodo|
      nodo.vm.hostname = n[:nombre]
      nodo.vm.network "private_network", ip: n[:ip]

      nodo.vm.provider "virtualbox" do |vb|
        vb.name = "bigdata-#{n[:nombre]}"
      end

      nodo.vm.provision "ansible" do |ansible|
        ansible.playbook = "provision/site.yml"
        ansible.compatibility_mode = "2.0"
      end
    end
  end
end

