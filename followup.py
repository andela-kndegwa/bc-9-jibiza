import json
import os
import time
from firebase import firebase
import requests
from shutil import copyfile
from termcolor import cprint
from pyfiglet import figlet_format

from question import Question

firebase = firebase.FirebaseApplication(
    'https://quizzapp-299a2.firebaseio.com/', None)


def load_quiz_info(quiz_file):
    """
    Load information from a quiz file.
    Return a tuple containing a list of questions and
    the time allocated for the quiz.
    """
    quiz_file = "quizzes/" + quiz_file + ".json"
    data = open(quiz_file, "r").read()
    quiz = json.loads(data)
    time_allocated = int(quiz["time_allocated"])
    questions = []
    for question in quiz["questions"]:
        text = question["question_text"]
        answer = question["answer"]
        try:
            # some questions may be open endend and thus may not have choices
            choices = question["choices"]
        except KeyError:
            choices = None
        questions.append(Question(text, answer, choices))
    return {"time_allocated": time_allocated, "questions": questions}


def import_quiz(path_to_quiz):
    """Import a quiz file to the quiz library."""
    try:
        quiz_name = json.loads(open(path_to_quiz).read())["name"]
    except FileNotFoundError:
        print("Invalid path supplied.")
        return
    copyfile(path_to_quiz, "quizzes/" + quiz_name + ".json")


def list_quizzes():
    """List all quizzes in the library."""
    try:
        quiz_files = [file.replace(".json", "")
                      for file in os.listdir("quizzes")]
        return quiz_files
    except FileNotFoundError:
        os.mkdir("quizzes")
        return []   # return empty list since no quizzes are available


def take_quiz(quiz_file):
    """Take the a quiz."""
    try:
        if quiz_file == "":
            print("You did not specify the quiz you want to take\n\
                To see the available quizzes, use the 'listquizzes command.")
            return
        quiz_info = load_quiz_info(quiz_file)
    except FileNotFoundError:
        print("{} does not exist on the Quiz Library".format(quiz_file))
        return

    questions = quiz_info["questions"]
    time_allocated = quiz_info["time_allocated"]
    graded_answers = []

    screen_width = get_terminal_width()
    cprint((quiz_file).center(screen_width), "yellow", attrs=["bold"])
    print("Time allocated for the quiz: {} seconds.".
          center(screen_width).format(time_allocated))
    input("Press Enter to start the quiz. ".center(screen_width))

    start_time = time.time()
    time_up = False
    for question in questions:
        if time.time() - start_time > time_allocated:
            time_up = True
            break
        draw_static_screen_question_mode(
            quiz_file, time.time() - start_time, time_allocated)
        print(question.to_string())
        user_answer = input("Answer: ")
        graded_answers.append(question.grade(user_answer))
        if graded_answers[-1] is False:
            cprint("WRONG!".center(screen_width),
                   "white", "on_red", attrs=["bold"])
        else:
            cprint("CORRECT!".center(screen_width),
                   "white", "on_green", attrs=["bold"])
        input("Press enter to proceed to the next question.")

    score = int(graded_answers.count(True) / len(questions) * 100)

    if time_up:
        draw_static_screen_question_mode(None, None, None, True)

    # summary
    cprint("""
              SUMMARY
    Total questions attempted: {a}
    Total questions available: {b}
    Correct attempts:          {c}
    Incorrect attempts:        {d}
    Your score:                {e}
    """.format(a=len(graded_answers),
               b=len(questions),
               c=graded_answers.count(True),
               d=graded_answers.count(False),
               e=score))


def upload_quiz(quiz_name):
    """Upload a quiz to the firebase repository."""
    try:
        quiz = open("quizzes/" + quiz_name + ".json", "r").read()
    except FileNotFoundError:
        print("Error: Quiz not found.")
        return

    try:
        url = '/quizzapp-299a2/Quizzes'
        firebase.post(url, json.loads(quiz))
    except requests.exceptions.ConnectionError:
        print("Quiz upload unsuccessful. Connection Error.")
        return
    print("Quiz uploaded successfully.")


def download_quiz(quiz_name):
    """Download a quiz from the firebase repository"""
    quizzes = download_quizzes()
    desired_key = None
    for key in quizzes.keys():
        if quizzes[key]["name"] == quiz_name:
            desired_key = key
            break
    if desired_key is None:
        print("'{}' is not in the online repository".format(quiz_name))
        return
    else:
        out_file = open("quizzes/" + quiz_name + ".json", "w")
        out_file.write(json.dumps(quizzes[desired_key]))
        out_file.close()
    print("Quiz downloaded successfully.")


def list_online_quizzes():
    """List all quizzes stored in the firebase repository."""
    quizzes = download_quizzes()
    try:
        for key in quizzes.keys():
            cprint(quizzes[key]["name"].center(
                get_terminal_width()), "green", attrs=["bold"])
    except AttributeError:
        print("There are no quizzes in the online repository.")


def download_quizzes():
    """Download quizzes from online repository"""
    online_quizzes = firebase.get('/quizzapp-299a2/Quizzes', None)
    return online_quizzes
