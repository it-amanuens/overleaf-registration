import re
import os
import ipaddress
import logging

import requests
from flask import Flask, render_template, Response, request, send_from_directory, abort

import overleaf
import yaml

# Load text content from YAML file
try:
    with open('texts.yaml', 'r') as file:
        TEXTS = yaml.safe_load(file)
except FileNotFoundError:
    logging.warning("texts.yaml not found, using default texts")
    TEXTS = {}  # Default empty dict

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration options
IP_FILTER_ENABLED = os.environ.get('IP_FILTER', 'true').lower() == 'true'
DEBUG_IP = os.environ.get('DEBUG_IP', 'false').lower() == 'true'

# Verification settings
VERIFICATION_QUESTION = os.environ.get('VERIFICATION_QUESTION', '')
VERIFICATION_KEY = os.environ.get('VERIFICATION_KEY', '')

# IP networks - comma-separated list of CIDR ranges
# IP networks - comma-separated list of CIDR ranges
ip_networks_str = os.environ.get('ALLOWED_NETWORKS', '0.0.0.0/0,::/0')  # All IPv4 and IPv6
UMU_NETWORKS = [network.strip() for network in ip_networks_str.split(',') if network.strip()]

if IP_FILTER_ENABLED and ip_networks_str == '0.0.0.0/0,::/0':
    logging.warning("⚠️ IP filtering using default 'allow all' configuration. Set ALLOWED_NETWORKS for security.")

# Allowed email domains - comma-separated list
email_domains_str = os.environ.get('ALLOWED_DOMAINS', 'student.umu.se,umu.se')
ALLOWED_DOMAINS = [domain.strip() for domain in email_domains_str.split(',') if domain.strip()]


def _is_umu_network(ip_address):
    """Check if the IP belongs to Umeå University network"""
    if DEBUG_IP:
        logging.info(f"Checking IP: {ip_address}")
    
    try:
        client_ip = ipaddress.ip_address(ip_address)
        for network in UMU_NETWORKS:
            if client_ip in ipaddress.ip_network(network):
                if DEBUG_IP:
                    logging.info(f"IP {ip_address} matched network {network}")
                return True
        
        if DEBUG_IP:
            logging.info(f"IP {ip_address} did not match any university networks")
        return False
    except ValueError:
        # Invalid IP format
        if DEBUG_IP:
            logging.error(f"Invalid IP format: {ip_address}")
        return False

def _check_email(email: str, allowed_domains=None) -> bool:
    """Validate email and optionally check if domain is in allowed list"""
    if not bool(re.fullmatch(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email)):
        return False
    
    if allowed_domains:
        domain = email.split('@')[-1].lower()
        return domain in allowed_domains
    
    return True

@app.route("/register", methods=["GET", "POST"])
def index() -> Response:
    # Get client IP, accounting for possible proxy
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Always print IP info if debug is enabled
    if DEBUG_IP:
        logging.info(f"Connection from IP: {client_ip}")
        logging.info(f"X-Forwarded-For: {request.headers.get('X-Forwarded-For')}")
        logging.info(f"Remote Addr: {request.remote_addr}")
    
    # Only check IP if IP filtering is enabled
    if IP_FILTER_ENABLED:
        if not _is_umu_network(client_ip):
            if DEBUG_IP:
                logging.warning(f"Access denied for IP: {client_ip}")
            return render_template("error.html", 
                                error=f"Registration is only available from University networks (register on campus). Your IP: {client_ip}"), 403
    
    if request.method == "GET":
        # Prepare template variables
        template_vars = {
            "title": TEXTS.get("title", "Overleaf Registration"),
            "header": TEXTS.get("header", "Overleaf Registration"),
            "email_placeholder": TEXTS.get("email_placeholder", "your.email@example.com"),
            "email_help_text": TEXTS.get("email_help_text", ""),
            "register_button": TEXTS.get("register_button", "Register"),
            "navbar_brand": TEXTS.get("navbar_brand", "Overleaf"),
        }
        
        # Add verification question if configured
        if VERIFICATION_QUESTION:
            template_vars["verification_question"] = VERIFICATION_QUESTION
            
        return render_template("register.html", **template_vars)
    
    elif request.method == "POST":
        email: str = request.form.get("email")
        
        # Check verification if configured
        if VERIFICATION_QUESTION:
            verification_key: str = request.form.get("verification_key")
            if not verification_key or verification_key.lower() != VERIFICATION_KEY.lower():
                return render_template("error.html", 
                                      title=TEXTS.get("error_title", "Registration Error"),
                                      header=TEXTS.get("header", "Overleaf Registration"),
                                      error=TEXTS.get("error_incorrect_key", "Incorrect verification key. Please try again.")), 400

        
        if not _check_email(email, ALLOWED_DOMAINS):
            return render_template("error.html", 
                          title=TEXTS.get("error_title", "Registration Error"),
                          header=TEXTS.get("header", "Overleaf Registration"),
                          error=TEXTS.get("error_invalid_email", "Invalid email or domain not allowed")), 400

        ol = overleaf.Overleaf(os.environ.get("OL_INSTANCE"))
        ol.login(os.environ.get("OL_ADMIN_EMAIL"), os.environ.get("OL_ADMIN_PASSWORD"))
        ol.register_user(email)
        ol.logout()
        success_msg = TEXTS.get("success_message", "Registration successful!")
        success_msg = success_msg.replace("{email}", f"<b>{email}</b>")

        return render_template("done.html", 
                      title=TEXTS.get("success_title", "Registration Complete"),
                      header=TEXTS.get("header", "Overleaf Registration"),
                      success_message=success_msg,
                      login_button=TEXTS.get("login_button", "Login"),
                      submitted_email=email)


@app.route("/register/static/<path:path>", methods=["GET"])
def serve_static_files(path) -> Response:
    return send_from_directory("static", path)