#!/usr/bin/python3
## ----------------------------------------------------------------------------
## Python Dependencies
import requests
import time
import datetime
import json, argparse
from fpdf import FPDF

## ----------------------------------------------------------------------------
t0= time.clock()
iq_url, iq_session = "",""

def getArguments():
	global iq_url, iq_session
	parser = argparse.ArgumentParser(description='Export Reporting Recommendations')
	parser.add_argument('-i','--publicId', help='PublicId for the Application', required=True)
	parser.add_argument('-u','--url', help='', default="http://localhost:8070", required=False)
	parser.add_argument('-a','--auth', help='', default="admin:admin123", required=False)
	parser.add_argument('-k','--insecure', help='Disable SSL Certificate validation',action='store_true', required=False)
	parser.add_argument('-s','--stage', help='', default="build", required=False)
	parser.add_argument('-l','--limiter', help='', default="10", required=False)
	
	args = vars(parser.parse_args())
	iq_url = args["url"]
	creds = args["auth"].split(":",1)
	iq_session = requests.Session()
	iq_session.auth = requests.auth.HTTPBasicAuth(creds[0], creds[1])
	if args["insecure"] == True:
                print('WARNING: Ignoring SSL Certificate Validation')
                iq_session.verify = False
	return args
#-----------------------------------------------------------------------------

#---------------------------------

class PDF(FPDF):
    def header(self):
        # Logo
        self.image('sonatype_logo.png', 10, 8, 33)
        # Times bold 15
        self.set_font('Times', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(100, 10, 'Remediation report', 1, 0, 'C')
        # Line break
        self.ln(20)

        # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Times', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

        #Chapter title
    def chapter_title(self, title):
        # Arial 12
        self.set_font('Times', 'B', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, '%s' % (title), 0, 1, 'L', 1)
        # Line break
        self.ln(0)

        #Chapter body
    def chapter_body(self, content_dict):
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        #self.multi_cell(0, 5, content)
        for field in content_dict:
            self.cell(0, 5, field+": "+content_dict[field], 1, 1)
        # Line break
        self.ln()

        #Print chapter
    def print_chapter(self, title, content):
        self.add_page('L')
        self.chapter_title(title)
        self.chapter_body(content)

    def print_list(self,data):
        self.cell()

    def fancy_table(this,header,data):
        #Colors, line width and bold font
        this.set_fill_color(255,0,0)
        this.set_text_color(255)
        this.set_draw_color(128,0,0)
        this.set_line_width(.3)
        this.set_font('Times','B')
        #Header
        w=[]
        column_no = len(header)
        page_width = 277 #magic number for A4 in mm
        column_width = page_width/column_no
        for i in range(0,column_no):
            w.append(column_width)
        for i in range(0,column_no):
                this.cell(w[i],7,header[i],1,0,'C',1)
        this.ln()
        #Color and font restoration
        this.set_fill_color(224,235,255)
        this.set_text_color(0)
        this.set_font('Times')
        #Data
        fill=0
        #print("This data: ")
        #print(len(data))
        #print(len(w))
        #print(column_no)
        for row in data:
            for i in range(0,column_no):
                this.cell(w[i],6,row[i],'LR',0,'C',fill)
                #print(row[i])
            this.ln()
            fill=not fill
        this.cell(sum(w),0,'','T')

    def dynamic_table(this,header,data):
        #Colors, line width and bold font
        this.set_fill_color(255,0,0)
        this.set_text_color(255)
        this.set_draw_color(128,0,0)
        this.set_line_width(.3)
        this.set_font('Times','B')
        #Header
        w=[]
        column_no = len(header)
        page_width = 277 #magic number for A4 in mm
        column_width = page_width/column_no
        for i in range(0,column_no):
            w.append(column_width)
        for i in range(0,column_no):
                this.cell(w[i],7,header[i],1,0,'C',1)
        this.ln()
        #Color and font restoration
        this.set_fill_color(224,235,255)
        this.set_text_color(0)
        this.set_font('Times')
        #Data
        fill=0
        #print("This data: ")
        #print(len(data))
        #print(len(w))
        #print(column_no)
        for row in data:
            for i in range(0,column_no):
                this.multi_cell(w[i],6,row[i],1,'L',fill)
                fill=not fill
                this.multi_cell(w[i],6,row[i+1],1,'L',fill)
                fill=not fill
                #this.multi_cell(w[i],6,row[i],0,'C',fill)
                #this.cell(w[i],6,row[i],'LR',0,'C',fill)
                #print(row[i])
            this.ln()
        this.cell(sum(w),0,'','T')

#---------------------------------

def output_pdf(pages, filename):
	pdf = FPDF()
	pdf.set_font('Times','B',12)
	for image in pages:
		pdf.add_page('L')
		pdf.set_xy(0,0)
		pdf.image(image, x = None, y = None, w = 0, h = 0, type = '', link = '')
	pdf.output(filename, 'F')


#---------------------------------


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
	pdf = PDF()
	pdf.alias_nb_pages()
	components = final
	#print(components)
	header = ['Current component (white), Recommended version (blue)']
	#header = ['Current component','Next with no violations','Next non-failing']
	data = []
	for component in components:
                if component["packageUrl"]["packageUrl"] is not None:
                        current = component["packageUrl"]["packageUrl"]
                        no_violations = component["recommendation"]["remediation"]["versionChanges"][0]["data"]["component"]["packageUrl"]
                        #non_failing = component["recommendation"]["remediation"]["versionChanges"][1]["data"]["component"]["packageUrl"]
                        aux = [current,no_violations]
                        #aux = [current,no_violations,non_failing]
                        data.append(aux)
                        #print(data)
	pdf.print_chapter('Remediation recommendations for '+str(publicId),"")
	pdf.set_font('Times','B',18)
	pdf.set_text_color(0,0,0)
	instructions = "Note: if the recommended version is the same as the current one, then there is no clean version without violations"
	pdf.multi_cell(0,7,instructions,0)
	pdf.ln(15)
	pdf.set_font('Times','',12)
	pdf.dynamic_table(header,data)
	pdf.output('./remediation_report.pdf', 'F')
	print("PDF generated -> remediation_report.pdf")

	
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
