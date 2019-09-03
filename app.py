"""Website where people can easily download IGCSE Past Papers"""
import os
import random
import shutil
import zipfile
import requests
from flask import Flask, request, Response, render_template, send_file, redirect
import papers_downloader
import config
from task_queue import Queue

APP = Flask(__name__)

def filter_args(args):
    """Removes "amp;" from request keys"""
    return {key.replace("amp;", ""):value for key, value in args.items()}

def convert_to_list(data):
    """Converts 2d list to a request"""
    return "?" + "&".join(["{}={}".format(key, value)
                           for key, value in data.items()])

def zipdir(task_id, filename):
    """Converts a dir to a zip"""
    zip_file = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)
    os.chdir(papers_downloader.config.DATA_FOLDER)
    os.chdir(task_id)
    for _, _, files in os.walk(os.getcwd()):
        for file in files:
            zip_file.write(file)
    os.chdir("..")
    os.chdir("..")

def download_papers(task_id, years_urls, to_filter):
    """Download all papers from a dict of paper urls (modified version)"""
    papers_done = 0
    papers_urls = {paper_name : paper_url
                   for year_url in years_urls
                   for paper_name, paper_url in papers_downloader.filter_papers(
                       papers_downloader.get_papers_urls(year_url),
                       to_filter).items()
                   }

    question_papers_folder = "{}/{}/{}".format(
        papers_downloader.config.DATA_FOLDER,
        task_id,
        papers_downloader.config.QUESTION_PAPERS_FOLDER
    )

    papers_downloader.mkdir(question_papers_folder)
    papers_downloader.mkdir("{}/{}/{}".format(
        papers_downloader.config.DATA_FOLDER,
        task_id,
        papers_downloader.config.MARK_SCHEME_FOLDER
    ))

    num = len(os.listdir(question_papers_folder))

    for paper_name, paper_url in papers_urls.items():
        _, paper_type = papers_downloader.get_paper_data(paper_name)


        if paper_type != "ms":
            folder = papers_downloader.config.QUESTION_PAPERS_FOLDER
        else:
            folder = papers_downloader.config.MARK_SCHEME_FOLDER

        data = requests.get(paper_url, headers=papers_downloader.config.HEADERS).content

        name = "{}/{}/{}/{}_{}.pdf".format(papers_downloader.config.DATA_FOLDER,
                                           task_id,
                                           folder,
                                           num,
                                           paper_name)

        with open(name+"_temp", "wb") as file:
            file.write(data)

        papers_downloader.remove_blank_pages(name+"_temp", name)
        os.remove(name+"_temp")
        papers_done += 1
        yield "data:" + str((papers_done/len(papers_urls))*100) + "\n\n"

    #zipdir(task_id,
           #"{}/{}.zip".format(papers_downloader.config.DATA_FOLDER, task_id))

    shutil.make_archive("{}/{}".format(papers_downloader.config.DATA_FOLDER, task_id),
                        'zip',
                        "{}/{}".format(papers_downloader.config.DATA_FOLDER, task_id))

    yield "data:/get_zip/{}/paper_bundle.zip\n\n".format(task_id)

@APP.route("/", methods=["POST", "GET"])
def homepage():
    """Homepage of the website"""

    angle = random.randint(-45, 45)
    color = random.choice(config.COLORS)
    if random.choice([True, False]):
        color = list(reversed(color))

    if request.method == "POST":
        to_convert = {
            "s" : request.form["summer_filter"].replace(" ", ","),
            "m" : request.form["feb_march_filter"].replace(" ", ","),
            "w" : request.form["winter_filter"].replace(" ", ","),
        }
        for key, value in request.form.items():
            to_convert[key] = value
        return redirect("/download" + convert_to_list(to_convert))

    return render_template("homepage.html", background_color=color, angle=angle)

@APP.route('/download')
def download_papers_page():
    """Where papers will be downloaded"""
    background_color = random.choice(random.choice(config.COLORS))
    progress_url = "/progress" + convert_to_list(request.args)
    return render_template("progress.html",
                           progress_url=progress_url,
                           background_color=background_color)

@APP.route("/get_zip/<task_id>/paper_bundle.zip")
def get_zip(task_id):
    """Returnes the zip file based on task id"""
    return send_file("{}/{}.zip".format(papers_downloader.config.DATA_FOLDER, task_id),
                     attachment_filename="papers.zip")

@APP.route("/progress")
def progress():
    """Where papers will be downloaded"""
    queue = Queue()

    papers_downloader.mkdir(papers_downloader.config.DATA_FOLDER)

    for task_id in queue.find_expired_tasks():
        shutil.rmtree("{}/{}".format(papers_downloader.config.DATA_FOLDER, task_id),
                      ignore_errors=True)
        os.remove("{}/{}.zip".format(papers_downloader.config.DATA_FOLDER, task_id))

    args = filter_args(request.args)
    paper_code = args[config.SUBJECT_CODE_ARG]
    start_year = int(args[config.START_YEAR_ARG])
    end_year = int(args[config.END_YEAR_ARG])

    to_filter = {key : args[key].split(",")
                 for key in ['s', 'm', 'w']}


    subject_url = papers_downloader.get_subject_url(paper_code)
    years_urls = papers_downloader.get_each_years_url(subject_url, start_year, end_year)

    task_id = queue.add_task()
    papers_downloader.mkdir("{}/{}".format(papers_downloader.config.DATA_FOLDER, task_id))

    return Response(
        download_papers(task_id, years_urls, to_filter),
        mimetype='text/event-stream'
    )

if __name__ == "__main__":
    APP.run(debug=True)