#!/usr/bin/env python3
import cloudconvert
import os
import ssl
import subprocess
ssl._create_default_https_context = ssl._create_unverified_context
def cc_convert(file):
	try:
		f = open("cc.json","r")
		list_ = f.read()
		cloudconvert.configure(api_key = list_, sandbox = False)
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

		# fix spaces WIP
		os.rename(file, file.replace(" ", "_"))
		file = file.replace(" ", "_")
		# do upload
		uploaded = cloudconvert.Task.upload(
			# file_name=os.path.join(os.path.dirname(os.path.realpath(__file__)), file), task=import_task)
			file_name=os.path.join(os.path.dirname(os.path.realpath(__file__)), file), task=import_task)
			# file_name = (file_name.replace(" ", "\\ "), task=import_task)
			# print (file_name)
		if uploaded:
			print("Uploaded file OK")
			# get exported url
			res = cloudconvert.Task.wait(id=export_task_id) # Wait for job completion
			exported = res.get("result").get("files")[0]
			res = cloudconvert.download(filename=os.path.splitext(file)[0]+'.pdf', url=exported['url'])
		warning = None
	except Exception as e:
		warning = str(e)
		res = None
	return res, warning

if __name__ == '__main__':
	# fix spaces in file
	test = '/Users/jandevera/Desktop/1.\ texty\ pro\ obálku.docx'
	res, warning = cc_convert(test)
	print (warning)
	print (res)
