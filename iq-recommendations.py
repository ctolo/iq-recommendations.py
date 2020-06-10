#!/usr/bin/python3
## ----------------------------------------------------------------------------
## Python Dependencies
import requests
import time
import datetime
import json, argparse

## ----------------------------------------------------------------------------
t0= time.clock()
iq_url, iq_session = "",""

def getArguments():
	global iq_url, iq_session
	parser = argparse.ArgumentParser(description='Export Reporting Recommendations')
	parser.add_argument('-i','--publicId', help='PublicId for the Application', required=True)
	parser.add_argument('-u','--url', help='', default="http://localhost:8070", required=False)
	parser.add_argument('-a','--auth', help='', default="admin:admin123", required=False)
	parser.add_argument('-s','--stage', help='', default="build", required=False)
	parser.add_argument('-l','--limiter', help='', default="10", required=False)
	args = vars(parser.parse_args())
	iq_url = args["url"]
	creds = args["auth"].split(":")
	iq_session = requests.Session()
	iq_session.auth = requests.auth.HTTPBasicAuth(creds[0], creds[1])
	return args
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def main():
	args = getArguments()
	publicId = args["publicId"]
	stageId = args["stage"]
	limiter = int(args["limiter"])

	applicationId = get_applicationId(publicId)
	reportId = get_reportId(applicationId, stageId)
	report = get_policy_violations(publicId, reportId)

	reportTime = get_epoch(report['reportTime'])
	final, ii, total = [], 0, report['counts']['totalComponentCount']
	if limiter > 0:
		print(f"Total components are {total}, but limiter is set to only {limiter}.")
		print("Pass in limiter of zero to get all results.")
		total = limiter
	for ii in range(total):
		t1 = int((time.clock() - t0)*100)
		print(f"Searching for {ii+1} of {total} components.")
		c = report['components'][ii]
		packageUrl = {"packageUrl": c["packageUrl"] } 
		recommendation = get_recommendation(packageUrl, applicationId, stageId)
		versions = get_last_version(packageUrl)
		final.append({
			"packageUrl": packageUrl, 
			"recommendation": recommendation, 
			"versions": versions
		})

	dumps(final)
	print("Final results saved to -> results.json")
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def pp(c):
	print( json.dumps(c, indent=4) )

def dumps(page, pretty = True, file_name = "results.json"):
	try:
		if pretty: page = json.dumps(page, indent=4)
		with open(file_name,"w+") as file:
			file.write(page)
	finally:
		return page

def handle_resp(resp, root=""):
	if resp.status_code != 200: 
		print(resp.text)
		return None
	node = resp.json()
	if root in node: node = node[root]
	if node == None or len(node) == 0: return None
	return node

def get_url(url, root=""):
	resp = iq_session.get(url)
	return handle_resp(resp, root)

def post_url(url, params, root=""):
	resp = iq_session.post(url, json=params)
	return handle_resp(resp, root)

def get_epoch(epoch_ms):
	dt_ = datetime.datetime.fromtimestamp(epoch_ms/1000)
	return dt_.strftime("%Y-%m-%d %H:%M:%S")

def get_applicationId(publicId):
	url = f'{iq_url}/api/v2/applications?publicId={publicId}'
	apps = get_url(url, "applications")
	if apps == None: return None
	return apps[0]['id']

def get_reportId(applicationId, stageId):
	url = f"{iq_url}/api/v2/reports/applications/{applicationId}"
	reports = get_url(url)
	for report in reports:
		if report["stage"] in stageId:
			return report["reportHtmlUrl"].split("/")[-1]

def get_policy_violations(publicId, reportId):
	url = f'{iq_url}/api/v2/applications/{publicId}/reports/{reportId}/policy'
	return get_url(url)

def get_recommendation(component, applicationId, stageId):
	url = f'{iq_url}/api/v2/components/remediation/application/{applicationId}?stageId={stageId}'
	return post_url(url, component)

def get_last_version(component):
	url = f"{iq_url}/api/v2/components/versions"
	return post_url(url, component)
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == "__main__":
	main()
