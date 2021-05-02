import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    '''
   Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app)

    '''
   Use the after_request decorator to set Access-Control-Allow

  '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    '''
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
    @app.route("/categories")
    def get_all_categories():
        categories = Category.query.all()

        if len(categories) == 0:
            abort(404)

        category_dict = {category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'categories': category_dict
        })

    '''
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 
  '''
    @app.route('/questions')
    def get_questions():
        questions = Question.query.all()
        formated = paginate_questions(request, questions)
        if(len(formated) == 0):
            abort(404)

        categories = Category.query.all()
        category_dict = [category.type for category in categories]
        return jsonify({
            "success": True,
            "questions": formated,
            "total_questions": len(questions),
            "categories": category_dict,
            "current_category": None
        })

    def paginate_questions(request, questions):
        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        formated = [question.format() for question in questions]
        current_quastions = formated[start:end]

        return current_quastions
    '''
  Create an endpoint to DELETE question using a question ID. 
  '''
    @app.route("/questions/<int:id>", methods=["DELETE"])
    def get_question(id):
        question = Question.query.filter(Question.id == str(id)).one_or_none()

        if question is None:
            abort(404)

        try:
            question.delete()

            questions = Question.query.all()
            formated = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'questions': formated,
                'deleted': id
            })
        except Exception as e:
            abort(422)
    '''
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.
  '''
    @app.route("/questions", methods=["POST"])
    def post_question():
        json_body = request.get_json()

        question_str = json_body.get('question', None)
        search_term = json_body.get('searchTerm', None)

        if question_str is not None:
            return insert_question(json_body)
        elif search_term is not None:
            return search_question(json_body)
        else:
            abort(400)

    def insert_question(json_body):
        try:
            question_str = json_body.get('question', None)
            answer = json_body.get('answer', None)
            difficulty = json_body.get('difficulty', None)
            category = json_body.get('category', None)

            if (question_str is None) or (answer is None) or (difficulty is None) or (category is None):
                abort(400)

            question = Question(question_str, answer, category, difficulty)

            question.insert()

            questions = Question.query.all()
            paged_questions = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'questions': paged_questions,
                'created': question.id,
                'question_created': question.question
            })
        except Exception as e:
            abort(422)
    '''
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 
  '''
    def search_question(json_body):
        search_term = json_body.get('searchTerm', '')
        questions = Question.query.filter(
            Question.question.ilike("%" + search_term + "%")).all()

        formated = [question.format() for question in questions]

        if len(formated) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': formated,
            "total_questions": len(formated),
            "current_category": None
        })
    '''
  Create a GET endpoint to get questions based on category. 
  '''
    @app.route("/categories/<int:id>/questions")
    def get_by_category(id):
        questions = Question.query.filter(Question.category == str(id)).all()
        questions_formated = [question.format() for question in questions]

        if len(questions_formated) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': questions_formated,
            "total_questions": len(questions_formated),
            "current_category": str(id)
        })

    '''
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 
  '''
    @app.route("/quizzes", methods=["POST"])
    def get_quizzes():
        json_body = request.get_json()

        previous_questions = json_body.get('previous_questions', None)
        quiz_category = json_body.get('quiz_category', None)
        category_id = quiz_category['id']

        if (previous_questions is None) or (quiz_category is None):
            abort(400)

        question = check_category(category_id, previous_questions)

        if question:
            return jsonify({
                "success": True,
                "question": question.format()
            })
        else:
            # if no more questions
            return jsonify({
                'success': True,
                "question": None
            })

    def check_category(category_id, previous_questions):
        # get from all categories
        questions = None
        if category_id == 0:
            questions = Question.query.all()
        else:
            questions = Question.query.filter(
                Question.category == str(category_id)).all()

        if len(questions) == 0:
            abort(404)

        return get_different_question(questions, previous_questions)

    def get_different_question(questions, previous_questions):
        random.shuffle(questions)
        question = None
        for question in questions:
            if question.id not in previous_questions:
                return question

    '''
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "We couldn't find what you are looking for!"
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Your request is not well formated!"
        }), 400

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            "success": False,
            "message": "Sorry, we coludn't proccess your request"
        }), 422

    return app
