# Ansible image factory

## Introduction

This collection of Ansible playbooks, scripts and files shows how to use Ansible to create customized
and hardened images for various operating systems on diverse platforms.

## Document structure

This document describes the general idea behind the image factory, and important files present 
in the root folder. Folders under the root may contain their own README files.

## Image factory basics

The image factory creates machine images in various steps. Some steps are platform dependent, some
steps apply to the operating system.

### Step 1
Step 1 creates the base VM. In public cloud environments, it uses an already existing image provided
by the cloud, like an Amazon AMI or Azure VM image. It is important to use the most standard version
as provided by the cloud provider or OS vendor. On VMware, we'll start with an ISO image file as 
provided by the OS vendor, and work from there

### Step 2

["Rule 6: there is no rule 6."](https://en.wikipedia.org/wiki/Bruces_sketch)

This step played a role in earlier iterations of the image factory. We decided not to change step 
numbers as we might need this extra step again in the future.

### Step 3

Step 3 makes sure all available OS updates have been installed. 'All available' does not necessarily 
mean 'latest from the vendor' as you might have update policies embedded in local repos or WSUS.

### Step 4

Step 4 installs VM agents for the platform, if they need to be installed. Think of VMware Tools, or 
Amazon SSM. On Azure, most base images already contain the VM-agent.

### Step 5

Step 5 configures the VM and adds libraries and agents, if you want to. At the end, hardening 
scripts are run.

### Step 10

Maybe you want to include tasks that will never be part of the main repository. You can do that under playbooks/custom.
See examples.

### Step 90

In this step the first image is created. It depends on the platform what needs to be done here

### Step 93

Next, we need to test the image. Ths means we'll deploy a VM from the newly created image and run
our baseline tests against it. If the test fail, the image is discarded. In any case, all tests are
logged for future reference.

### Step 96 

If the VM passed the tests, we need to distribute the image. In most cases, this means we need to
create a new image from the base VM.

### Step 99

After the image has been put in its final destination, we can delete the source VM. In case of any 
failure in the previous steps, we need to remove the VM as well. This step takes care of that.

## Known issues

The Windows AWS regularly show WinRM failures. Sometimes it's just the time in the Windows machine
that's a few minutes ahead, sometimes the password doesn't 

## Important files

### `Jenkinsfile`

This file defines the parametrized pipeline definition for use in Jenkins. Basically it's just
a retry loop, in which three consecutive attempts to create an image are carried out. If an attempt
fails, it makes sure the intermediate VM that was created is being removed.

### `Dockerfile`

This file is used to create the final Dockerized version of the image factory.

### dotfiles and scripts folder

All dotfiles like .editorconfig, .gitignore and so on can be modified to your own taste. 
`.pre-commit-config` contains a sample configuration that makes sure the Ansible YAML files are linted, 
a TODO.md file is generated and that Ansible vault files are encrypted. It uses two scripts in the 
scripts folder, and you need to have ansible-lint and pre-commit installed.

## License

GNU General Public License v3.0

See [COPYING.md](./COPYING.md) to see the full text.
