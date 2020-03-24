#!/usr/bin/env python3
import cloudconvert
import os
# FIX for ssl bug...
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
cloudconvert.configure(api_key = 0, sandbox = False)
# test = '/Users/jandevera/Desktop/1.docx'
def cc_convert(file):
	job = cloudconvert.Job.create(payload={
		'tag': 'convert_to_pdf',
		'tasks': {
			'import-it': {
				'operation': 'import/upload'
			},
			'convert-my-file': {
				'input': 'import-it',
				'operation': 'convert',
				'output_format': 'pdf'
			},
			'export-it': {
				'input': 'convert-my-file',
				'operation': 'export/url'
			}
		}
	})
	import_task = None
	for task in job["tasks"]:
		task_name = task.get("name")
		if task_name == "import-it":
			import_task = task
		if task_name == "export-it":
			export_task = task
	
	import_task_id = import_task.get("id")
	export_task_id = export_task.get("id")
	# fetch the finished task
	import_task = cloudconvert.Task.find(id=import_task_id)
	# do upload
	uploaded = cloudconvert.Task.upload(
		file_name=os.path.join(os.path.dirname(os.path.realpath(__file__)), file), task=import_task)
	try:
		if uploaded:
			print("Uploaded file OK")
			# get exported url
			res = cloudconvert.Task.wait(id=export_task_id) # Wait for job completion
			exported = res.get("result").get("files")[0]
			print ('EX' + str(exported))
			res = cloudconvert.download(filename=os.path.splitext(file)[0]+'.pdf', url=exported['url'])
	except:
		print("An exception occurred" + res)
	return res

if __name__ == '__main__':
	cc_convert(test)