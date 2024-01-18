### useful documents
### https://www.cloudservices.store/cp/knowledgebase/76/How-To-Install-ElasticSearch-7.x-on-CentOS-7-or-RHEL-7.html


import os
import textwrap

def run_command(command):
    os.system(command)

def find_package_manager():
    if os.path.exists('/usr/bin/yum'):
        return 'yum'
    elif os.path.exists('/usr/bin/dnf'):
        return 'dnf'
    elif os.path.exists('/usr/bin/apt'):
        return 'apt'
    else:
        return False

def package_installer(package_name):
    package_manager = find_package_manager()
    if not package_manager:
        print('Package manager not found')
        exit(1)
    if isinstance(package_name, list):
        for package in package_name:
            os.system('{} install -y {}'.format(package_manager, package))
    else:
        os.system('{} install -y {}'.format(package_manager, package_name))

def update_all_package(pkmanager):
    if pkmanager == 'yum':
        os.system('yum update -y')
    elif pkmanager == 'dnf':
        os.system('dnf update -y')
    elif pkmanager == 'apt':
        os.system('apt update -y')
    else:
        print('Package manager not found')
        exit(1)

def change_current_dir(new_dir):
    os.chdir(new_dir)

def create_elk_repo():
    # Add the repository definition to a file
    repo_data = textwrap.dedent('''
    [elasticsearch-7.x]
    name=Elasticsearch repository for 7.x packages
    baseurl=https://artifacts.elastic.co/packages/7.x/yum
    gpgcheck=1
    gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
    enabled=1
    autorefresh=1
    type=rpm-md
    ''')

    with open('/etc/yum.repos.d/elasticsearch.repo', 'w') as f:
        f.write(repo_data)

def disable_selinux():
    # Check if SELinux is already disabled
    current_status = os.popen('getenforce').read().strip()
    if current_status == 'Disabled':
        print('SELinux is already disabled')
        return

    # Disable SELinux temporarily
    os.system('setenforce 0')

    # Update SELinux configuration file to disable SELinux permanently
    with open('/etc/selinux/config', 'r') as f:
        lines = f.readlines()

    with open('/etc/selinux/config', 'w') as f:
        for line in lines:
            if 'SELINUX=' in line:
                f.write('SELINUX=disabled\n')
            else:
                f.write(line)

    print('SELinux is disabled')

    print('Please reboot the system to apply changes')

def get_ipv4_address():
    return os.popen("hostname -I | cut -d ' ' -f1").read().strip()


## Main
disable_selinux()
package_installer('wget nano epel-release')
package_installer('htop')
update_all_package(find_package_manager())

# Install Java
package_installer('java-11-openjdk-devel')

# Import the gpg key
run_command('rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch')

# Create the ELK repository
create_elk_repo()

# Install elk
package_installer("elasticsearch")

# Configure Elasticsearch
change_current_dir('/etc/elasticsearch')
run_command('cp elasticsearch.yml elasticsearch.yml.bak')
run_command('cp jvm.options jvm.options.bak')

# Update elasticsearch.yml
with open('elasticsearch.yml', 'r') as f:
    lines = f.readlines()

with open('elasticsearch.yml', 'w') as f:
    for line in lines:
        if 'network.host:' in line:
            f.write('network.host: 127.0.0.1,{}\n'.format(get_ipv4_address()))
        elif 'http.port:' in line:
            f.write('http.port: 9200\n')
        elif '#cluster.initial_master_nodes:' in line:
            f.write('cluster.initial_master_nodes: ["node-1"]\n')
        elif '#cluster.name:' in line:
            f.write('cluster.name: pspro-elk\n')
        elif '#node.name:' in line:
            f.write('node.name: node-1\n')
        else:
            f.write(line)

# Update jvm.options
with open('jvm.options', 'r') as f:
    lines = f.readlines()

with open('jvm.options', 'w') as f:
    for line in lines:
        if '-Xms1g' in line:
            f.write('-Xms512m\n')
        elif '-Xmx1g' in line:
            f.write('-Xmx512m\n')
        else:
            f.write(line)


# Start and enable Elasticsearch service
run_command('systemctl daemon-reload')
run_command('systemctl enable elasticsearch')
run_command('systemctl start elasticsearch')
run_command('curl -X GET "localhost:9200/"')