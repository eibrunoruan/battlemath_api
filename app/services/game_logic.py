from app.models import Question
import random

def generate_question(categories):
    questions = Question.query.filter(Question.category.in_(categories)).all()
    if not questions:
        return None

    question = random.choice(questions)

    return {
        'id': question.id,
        'category': question.category,
        'text': question.text,
        'options': {
            'A': question.option_a,
            'B': question.option_b,
            'C': question.option_c,
            'D': question.option_d
        }
    }

def validate_answer(question_id, selected_option):
    question = Question.query.get(question_id)
    if not question:
        return False

    return selected_option.upper() == question.correct_option.upper()
