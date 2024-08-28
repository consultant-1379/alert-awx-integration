import configparser
import http.client
import http.server
import json
import requests
import urllib.parse

AWX_CONF_FILE = '/etc/awx.conf'
BIND_ADDRESS = '0.0.0.0'
BIND_PORT = 9099

class Handler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        """
        Method to receive all POST requests from external address
        :return: None
        """
        # Read and parse the request body:
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        body = body.decode("utf-8")
        body = json.loads(body)
        print("Alert manager request:\n%s" % self.indent(body))

        # Send an empty response:
        self.send_response(200)
        self.end_headers()

        # Process all the alerts:
        alerts = body["alerts"]
        for alert in alerts:
            self.process_alert(alert)

    def process_alert(self, alert):
        """
        Process all the alerts received from Alertmanager by forwarding to AWX
        :params: alert 
        :return: None
        """
        # Read all AWX config and set url
        url = 'http://' + awx_config['AWX_HOST'] + ':' +awx_config['AWX_PORT']
        token = awx_config['AWX_TOKEN']
        project = awx_config['AWX_PROJECT']
        template = awx_config['AWX_TEMPLATE']

        # Send the request to find the job template:
      
        template_response = requests.get(url + '/api/v2/job_templates/',
                                params={"name": template,
            "project__name": project},
                                headers = {
                "Content-type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer %s" % token
            })

        if template_response.status_code != 200:
            print("Failed to get template ID: \n%s" % template_response.status_code)
	    return

        # Get the identifier of the job template:
        template_id = template_response.json()["results"][0]["id"]

        # Send the request to launch the job template, including all the labels, status and annotations
        # of the alert as extra variables for the AWX job template:
        status = {"status":alert["status"]}
        extra_vars = alert["labels"]
        extra_vars.update(alert["annotations"])
        extra_vars.update(status)
        extra_vars = json.dumps(extra_vars)
        post_data = {"extra_vars": extra_vars}

        print(post_data)
        post_response = requests.post(url + "/api/v2/job_templates/%s/launch/" % template_id,
                      headers={
                "Content-type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer %s" % token},
                      json = post_data)
        print("AWX Response: %s" % self.indent(post_response.json()))
        
        if post_response.status_code != 201:
            print("Failed to POST to AWX: \n%s" % post_response.status_code)

    def indent(self, data):
        return json.dumps(data, indent=2)

#Read the AWX config file for properties in provided section
def parse_config(section):
    """
    Parse all the conf from AWX_CONF file and set as global dict
    :params: section to parse
    :return: None
    """
    global awx_config
    try:
        config = configparser.ConfigParser()
        config.read(AWX_CONF_FILE)
        awx_config = config[section]
    except configparser.Error as exp:
        raise Exception(str.format("Error parsing config.\n{}", str(exp)))

parse_config('AWX')

# Start the web server:
address = (BIND_ADDRESS, BIND_PORT)
# Need to use https once the configuration is done for all monitoring components as http is not secure
server = http.server.HTTPServer(address, Handler)
server.serve_forever()
