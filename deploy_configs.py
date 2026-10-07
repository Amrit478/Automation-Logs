#!/usr/bin/env python3
import os
import sys
import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from concurrent.futures import ThreadPoolExecutor

def load_data(vars_file="vars.yml"):
    try:
        with open(vars_file, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[!] Error: {vars_file} not found.", file=sys.stderr)
        sys.exit(1)

def render_config(env, template_name, global_vars, device):
    template = env.get_template(template_name)
    return template.render(
        collector_ip=global_vars.get("collector_ip"),
        netflow_export_port=global_vars.get("netflow_export_port", 2055),
        syslog_port=global_vars.get("syslog_port", 1514),
        device=device
    )

def deploy_device(device, config_str, global_creds):
    hostname = device.get("hostname", "Unknown")
    ip = device.get("ip")
    device_type = device.get("device_type", "cisco_ios")

    username = device.get("username", global_creds.get("username"))
    password = device.get("password", global_creds.get("password"))
    secret = device.get("secret", global_creds.get("secret"))

    device_params = {
        "device_type": device_type,
        "host": ip,
        "username": username,
        "password": password,
        "secret": secret if secret else "",
        "timeout": 25,
        "fast_cli": False,
    }

    config_commands = [
        line.strip() 
        for line in config_str.splitlines() 
        if line.strip() and not line.strip().startswith("!")
    ]

    print(f"[*] [{hostname}] Connecting to {ip}...")
    try:
        with ConnectHandler(**device_params) as net_connect:
            if secret and not net_connect.check_enable_mode():
                net_connect.enable()
            
            print(f"[*] [{hostname}] Pushing configuration commands...")
            output = net_connect.send_config_set(config_commands)
            
            print(f"[*] [{hostname}] Saving configuration...")
            net_connect.save_config()
            
            print(f"[+] [{hostname}] Deployed successfully!")
            return (hostname, True, output)

    except NetmikoTimeoutException:
        print(f"[!] [{hostname}] Error: Connection timeout to {ip}.", file=sys.stderr)
        return (hostname, False, "Timeout")
    except NetmikoAuthenticationException:
        print(f"[!] [{hostname}] Error: Authentication failed for {ip}.", file=sys.stderr)
        return (hostname, False, "Auth Failure")
    except Exception as e:
        print(f"[!] [{hostname}] Unexpected Error: {e}", file=sys.stderr)
        return (hostname, False, str(e))

def main():
    data = load_data("vars.yml")
    global_creds = data.get("ssh_credentials", {})
    devices = data.get("devices", [])

    env = Environment(
        loader=FileSystemLoader("."),
        trim_blocks=True,
        lstrip_blocks=True
    )

    os.makedirs("output", exist_ok=True)
    deployment_tasks = []

    for device in devices:
        config_str = render_config(env, "cisco_logging.j2", data, device)
        with open(os.path.join("output", f"{device['hostname']}.cfg"), "w") as f:
            f.write(config_str)
        deployment_tasks.append((device, config_str))

    print(f"[*] Deploying to {len(deployment_tasks)} Cisco IOL nodes...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(deploy_device, dev, cfg, global_creds)
            for dev, cfg in deployment_tasks
        ]
        for future in futures:
            future.result()

if __name__ == "__main__":
    main()