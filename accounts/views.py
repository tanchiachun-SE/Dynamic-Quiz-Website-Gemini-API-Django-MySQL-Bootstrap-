from pyexpat.errors import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .models import Account, Questionbank, Assignment, StudentAnswer,StudentResult
from .forms import QuestionBankForm, AssignmentForm,  CustomQuestionBankForm 
from django.core.paginator import Paginator
from django.db.models import Case, When
from django.db.models import Count, Sum, F
from django.urls import reverse
import openpyxl
from django.http import HttpResponse
from django.utils import timezone  # Import timezone for handling datetime
import json
from io import BytesIO 
import google.generativeai as genai
GOOGLE_API_KEY = ""
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-3-flash-preview")

# Create your views here.

#home 

def home(request):
    return render(request, 'home.html')

# code of register and login

def index(request):
    is_login = request.session.get('is_login', None)
    if not is_login:
        return render(request, 'login.html')
    user_id = request.session.get('user_id')
    account = Account.objects.get(id=user_id)
    if account.customer_type == 0:
        return render(request, 'student_info')
    elif account.customer_type == 1:
        return render(request, 'teacher_info') 

def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if not username or not password:
            return render(request, 'login.html', {'error': 'info not complete'})
        if not Account.objects.filter(username=username).exists():
            return render(request, 'login.html', {'error': 'username not exists'})
        
        account = Account.objects.filter(username=username)[0]
        if not check_password(password, account.password):
            return render(request, 'login.html', {'error': 'password error'})
        
        request.session['is_login'] = True
        request.session['user_id'] = account.id
        request.session['username'] = account.username
        request.session['customer_type'] = account.customer_type

        # depand on user type go to which page
        if account.customer_type == 0:
            return redirect('student_dashboard')

        elif account.customer_type == 1:
            return redirect('assignment_list')

def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    if request.method == 'POST':
        username = request.POST.get('username', None)
        email = request.POST.get('email', None)
        password = request.POST.get('password', None)
        password_again = request.POST.get('password-again', None)
        typ = request.POST.get('cus_typ', None)
        if not username or not email or not password or not password_again or not typ:
            return render(request, 'register.html', {'error': 'info not complete'})
        if password_again !=password:
            return render(request, 'register.html', {'error': 'password not same'})
        if Account.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'username exists'})
        if Account.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'email exists'})
        Account(username=username, email=email, password=make_password(password), customer_type=typ).save()
        return redirect('login')

def logout(request):
    # Clear all session data
    request.session.clear()
    # Invalidate the session
    request.session.flush() 
    # Delete the session cookie
    request.session.delete()
    # Redirect to login page
    return redirect('login')

def student_info(request):
    return render(request, 'student_info.html')

#Assignment

def assignment_list(request):
    is_login = request.session.get('is_login', None)
    if not is_login:
        return redirect('login')
        
    # Check if user is a teacher (customer_type == 1)
    customer_type = request.session.get('customer_type')
    if customer_type != 1:
        return redirect('student_dashboard')
    assignments = Assignment.objects.annotate(
        total_questions=Count('questionbank'),

    )

    return render(request, 'assignment_list.html', {'assignments': assignments})

def assignment_create(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assignment_list')
    else:
        form = AssignmentForm()
    return render(request, 'assignment_create.html', {'form': form})

def assignment_delete(request,aid):
    assignments = Assignment.objects.get(aid=aid)
    assignments.delete()
    return redirect("assignment_list")

def assignment_update(request, aid):
    assignments = get_object_or_404(Assignment, aid=aid)
    if request.method == "POST":
        form = AssignmentForm(request.POST, instance=assignments)
        if form.is_valid():
            form.save()
            return redirect('assignment_list')
    else:
        form = AssignmentForm(instance=assignments)
        
    return render(request, 'assignment_update.html', {'form': form, 'aid': aid,'assignments': assignments})

# question bank

def question_list(request):
    is_login = request.session.get('is_login', None)
    if not is_login:
        return redirect('login')
        
    # Check if user is a teacher (customer_type == 1)
    customer_type = request.session.get('customer_type')
    if customer_type != 1:
        return redirect('student_dashboard')
    questions = Questionbank.objects.all()
    for question in questions:
        question.is_published = question.assignment.published
    return render(request, 'question_list.html', {'questions': questions})

def question_create(request):
    if request.method == 'POST':
        form = QuestionBankForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('question_list')
    else:
        form = QuestionBankForm()
    return render(request, 'question_create.html', {'form': form})

def yes_no_create(request):
    if request.method == 'POST':
        form = CustomQuestionBankForm(request.POST)  # Use the custom form
        if form.is_valid():
            form.save()
            return redirect('question_list')
    else:
        form = CustomQuestionBankForm()  # Use the custom form
        
    return render(request, 'yes_no_create.html', {'form': form})

def question_delete(request,qid):
    questions = Questionbank.objects.get(qid=qid)
    questions.delete()
    return redirect("question_list")

def question_update(request, qid):
    questions = get_object_or_404(Questionbank, qid=qid)
    if request.method == "POST":
        form = QuestionBankForm(request.POST, instance=questions)
        if form.is_valid():
            form.save()
            return redirect('question_list')
    else:
        form = QuestionBankForm(instance=questions)
    return render(request, 'question_update.html', {'form': form, 'qid': qid})

#student answer the assignment

def student_dashboard_view(request):    
    is_login = request.session.get('is_login', None)
    if not is_login:
        return redirect('login')
        
    # Check if user is a teacher (customer_type == 1)
    customer_type = request.session.get('customer_type')
    if customer_type != 0:
        return redirect('assignment_list')
    
    assignments = Assignment.objects.annotate(
        total_questions=Count('questionbank'),

    )
    dict = {
'Assignment': Assignment.objects.filter(published=True).count(),  # Filter for published assignments
        'Questionbank': Questionbank.objects.filter(assignment__published=True).count(),  # Filter for published question banks
    }
    return render(request, 'student_dashboard.html', context=dict)


def student_exam_view(request):
    user_id = request.session.get('user_id')
    account = get_object_or_404(Account, id=user_id)
    assignments = Assignment.objects.filter(published=True)
    completed_assignments = StudentResult.objects.filter(account=account).values_list('assignment__aid', flat=True)
    context = {
        'Assignments': assignments,
        'completed_assignments': list(completed_assignments),  # Convert to list for easier comparison in template
    }
    return render(request, 'student_exam.html', context)


def take_exam_view(request, aid):
    
    Assignments = Assignment.objects.get(aid=aid)
    questionbank = Questionbank.objects.all().filter(assignment=Assignments)
    total_questions = questionbank.count()
    total_marks = 0
    for q in questionbank:
        total_marks=total_marks + q.score

    return render(request, 'take_exam.html', {'Assignments': Assignments, 'total_questions': total_questions, 'total_marks': total_marks,'questionbank':questionbank })

def start_exam_view(request, aid):
    Assignments = Assignment.objects.get(aid=aid)
        # depand on mechanism type go to which page
    if Assignments.mechanism_type == 0:
            return redirect('random_view',aid=aid)
    elif Assignments.mechanism_type == 1:
            return redirect('fixed_view',aid=aid)
    elif Assignments.mechanism_type == 2:
            return redirect('dynamic_view',aid=aid)

def random_view(request, aid):
    assignment = get_object_or_404(Assignment, aid=aid)
    questionbank = Questionbank.objects.filter(assignment=assignment)
    
    user_id = request.session.get('user_id')
    account = get_object_or_404(Account, id=user_id)
    
    paginator = Paginator(questionbank, 1)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        current_question = page_obj.object_list[0]
        student_answer = request.POST.get('answer')
        
        # Check if answer already exists for this question
        existing_answer = StudentAnswer.objects.filter(
            account=account,
            assignment=assignment,
            question=current_question
        ).exists()
        
        # Only save if no existing answer
        if not existing_answer:
            start_time = request.session.get('question_start_time')
            if start_time:
                elapsed_time = (timezone.now() - timezone.datetime.fromisoformat(start_time)).total_seconds()
                time_allowed = get_time_allowed(current_question.level)
                
                if elapsed_time <= time_allowed:
                    StudentAnswer.objects.create(
                        account=account,
                        assignment=assignment,
                        question=current_question,
                        answer=student_answer
                    )
                else:
                    StudentAnswer.objects.create(
                        account=account,
                        assignment=assignment,
                        question=current_question,
                        answer=None
                    )
        
        if page_obj.has_next():
            return redirect(f'/random-exam/{aid}/?page={page_obj.next_page_number()}')
        else:
            student_answers = StudentAnswer.objects.filter(
                account=account,
                question__assignment=assignment
            )
            correct_answers = student_answers.filter(answer=F('question__answer'))
            total_marks = correct_answers.aggregate(Sum('question__score'))['question__score__sum'] or 0
            
            StudentResult.objects.create(
                account=account,
                assignment=assignment,
                total_marks=total_marks
            )
            return redirect('student_exam')
    
    request.session['question_start_time'] = timezone.now().isoformat()
    
    context = {
        'assignment': assignment,
        'page_obj': page_obj,
        'time_allowed': get_time_allowed(page_obj.object_list[0].level),
    }
    
    return render(request, 'random_exam.html', context)

def get_time_allowed(level):
    if level == 'easy':
        return 30
    elif level == 'middle':
        return 60
    elif level == 'hard':
        return 80
    return 0

def fixed_view(request, aid):
    assignment = get_object_or_404(Assignment, aid=aid)
    # Order questions by difficulty
    questionbank = Questionbank.objects.filter(assignment=assignment).order_by(
        Case(
            When(level='easy', then=0),
            When(level='middle', then=1),
            When(level='hard', then=2),
        ),
        'qid'  # Secondary ordering by question ID to ensure consistent order
    )
    
    # Get the current user
    user_id = request.session.get('user_id')
    account = get_object_or_404(Account, id=user_id)
    
    # Create a paginator object
    paginator = Paginator(questionbank, 1)  # Show 1 question per page
    
    # Get the page number from the request's GET parameters
    page_number = request.GET.get('page', 1)
    
    # Get the Page object for the current page
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        # Get the current question
        current_question = page_obj.object_list[0]
        
        # Get the student's answer
        student_answer = request.POST.get('answer')
        
                # Check if answer already exists for this question
        existing_answer = StudentAnswer.objects.filter(
            account=account,
            assignment=assignment,
            question=current_question
        ).exists()
        
        # Only save if no existing answer
        if not existing_answer:
        # Check if the answer was submitted within the time limit
            start_time = request.session.get('question_start_time')
            if start_time:
                elapsed_time = (timezone.now() - timezone.datetime.fromisoformat(start_time)).total_seconds()
                time_allowed = get_time_allowed(current_question.level)
            
                if elapsed_time <= time_allowed:
                    StudentAnswer.objects.create(
                    account=account,
                    assignment=assignment,
                    question=current_question,
                    answer=student_answer
                    )
                else:
                    StudentAnswer.objects.create(
                    account=account,
                    assignment=assignment,
                    question=current_question,
                    answer=None
                    )

	# Check if it's the last question
          
        # Check if it's the last question
        if page_obj.has_next():
            return redirect(f'/fixed-exam/{aid}/?page={page_obj.next_page_number()}')
        else:
            # Calculate total marks
            student_answers = StudentAnswer.objects.filter(
                account=account,
                question__assignment=assignment
            )
            correct_answers = student_answers.filter(answer=F('question__answer'))
            total_marks = correct_answers.aggregate(Sum('question__score'))['question__score__sum'] or 0
            
            # Save the total marks
            StudentResult.objects.create(
                account=account,
                assignment=assignment,
                total_marks=total_marks
            )
            
            return redirect('student_exam')  # Redirect to a results page

    # Set the start time for the current question    
    request.session['question_start_time'] = timezone.now().isoformat()

    
    context = {
        'assignment': assignment,
        'page_obj': page_obj,
        'time_allowed': get_time_allowed(page_obj.object_list[0].level),

    }
    
    return render(request, 'random_exam.html', context)

def dynamic_view(request, aid):
    assignment = get_object_or_404(Assignment, aid=aid)
    user_id = request.session.get('user_id')
    account = get_object_or_404(Account, id=user_id)
    
    # Get the current question level from session or default to 'easy'
    current_level = request.session.get('current_level', 'easy')
    
    # Get the current question count from session or default to 0
    question_count = request.session.get('question_count', 0)
    
    # If the student has answered 5 questions, calculate the result
    if question_count >= 5:
        student_answers = StudentAnswer.objects.filter(
            account=account,
            question__assignment=assignment
        )
        correct_answers = student_answers.filter(answer=F('question__answer'))
        total_marks = correct_answers.aggregate(Sum('question__score'))['question__score__sum'] or 0
        
        # Save the total marks
        StudentResult.objects.create(
            account=account,
            assignment=assignment,
            total_marks=total_marks
        )
        
        # Clear session data
        del request.session['current_level']
        del request.session['question_count']
        
        return redirect('student_exam')  # Redirect to a results page
    
    # Get a question of the current level that the student hasn't answered yet
    answered_questions = StudentAnswer.objects.filter(account=account).values_list('question_id', flat=True)
    question = Questionbank.objects.filter(assignment=assignment, level=current_level).exclude(qid__in=answered_questions).first()
    
    if request.method == 'POST':
        student_answer = request.POST.get('answer')
        start_time = request.session.get('question_start_time')
        
        if start_time:
            elapsed_time = (timezone.now() - timezone.datetime.fromisoformat(start_time)).total_seconds()
            time_allowed = get_time_allowed(current_level)
            
            if elapsed_time <= time_allowed:
                StudentAnswer.objects.create(
                    account=account,
                    question=question,
                    answer=student_answer,
                    assignment=assignment
                )
                
        # Check if the answer is correct
                if student_answer == question.answer:
                    # Move to the next level if correct
                    if current_level == 'easy':
                        current_level = 'middle'
                    elif current_level == 'middle':
                        current_level = 'hard'
                else:
                    # Adjust level based on the current level and incorrect answer
                    if current_level == 'middle':
                        current_level = 'easy'
                    elif current_level == 'hard':
                        current_level = 'middle'
                    # Stay on the same level if incorrect, but get a different question
                    question = Questionbank.objects.filter(assignment=assignment, level=current_level).exclude(qid__in=answered_questions).first()
            else:
                # Time's up, record a blank answer
                StudentAnswer.objects.create(
                    account=account,
                    question=question,
                    answer=None,
                    assignment=assignment
                )
                if current_level == 'middle':
                    current_level = 'easy'
                elif current_level == 'hard':
                    current_level = 'middle'


        # Increment the question count
        question_count += 1
        
        # Update session data
        request.session['current_level'] = current_level
        request.session['question_count'] = question_count
        
        return redirect('dynamic_view', aid=aid)
    
    # Set the start time for the current question
    request.session['question_start_time'] = timezone.now().isoformat()

    
    context = {
        'assignment': assignment,
        'question': question,
        'time_allowed': get_time_allowed(current_level),

    }
    
    return render(request, 'dynamic_exam.html', context)


    


#student result in table 

def student_results(request):
    is_login = request.session.get('is_login', None)
    if not is_login:
        return redirect('login')
        
    # Check if user is a teacher (customer_type == 1)
    customer_type = request.session.get('customer_type')
    if customer_type != 1:
        return redirect('student_dashboard')
    
    results = StudentResult.objects.all().select_related('account', 'assignment')
    
    # Add a URL for viewing detailed results
    for result in results:
        result.detail_url = reverse('student_result_detail', args=[result.id])
        result.total_marks_all_questions = StudentAnswer.objects.filter(
            account=result.account,
            assignment=result.assignment
        ).aggregate(total_marks=Sum('question__score'))['total_marks'] or 0
    
    return render(request, 'student_results.html', {'results': results})

def student_result_detail(request, result_id):
    is_login = request.session.get('is_login', None)
    if not is_login:
        return redirect('login')
        
    # Check if user is a teacher (customer_type == 1)
    customer_type = request.session.get('customer_type')
    if customer_type != 1:
        return redirect('student_dashboard')
    result = get_object_or_404(StudentResult, id=result_id)
    student_answers = StudentAnswer.objects.filter(
        account=result.account,
        question__assignment=result.assignment
    ).select_related('question')
    
    detailed_answers = []
    for answer in student_answers:
        options_mapping = {
            'Option1': answer.question.option1,
            'Option2': answer.question.option2,
            'Option3': answer.question.option3,
            'Option4': answer.question.option4,
        }
        
        detailed_answers.append({
            'question_text': answer.question.question,
            'student_answer': options_mapping.get(answer.answer, answer.answer),  # Get actual option text
            'correct_answer': options_mapping.get(answer.question.answer, answer.question.answer),  # Get actual option text
            'is_correct': answer.answer == answer.question.answer,
            'score': answer.question.score if answer.answer == answer.question.answer else 0,
        })
    
    context = {
        'result': result,
        'detailed_answers': detailed_answers,
        'total_questions': len(detailed_answers),
        'correct_answers': sum(1 for a in detailed_answers if a['is_correct']),
    }
    
    return render(request, 'student_result_detail.html', context)

#download xlsm

def download_xlsm_s(request):
    # Create a workbook and add a worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Student Results"

    # Add headers
    headers = ['Account Name', 'Assignment', 'Marks of Student', 'Total Marks', 'Completed At']
    worksheet.append(headers)

    # Fetch results from the database
    results = StudentResult.objects.all().select_related('account', 'assignment')

    # Add data to the worksheet
    for result in results:
        result.total_marks_all_questions = StudentAnswer.objects.filter(
            account=result.account
        ).aggregate(total_marks=Sum('question__score'))['total_marks'] or 0
        
        # Convert completed_at to naive datetime
        completed_at_naive = result.completed_at.replace(tzinfo=None)  # Remove timezone info
        
        worksheet.append([
            result.account.username,
            result.assignment.assignment_name,
            result.total_marks,
            result.total_marks_all_questions,
            completed_at_naive,  # Use the naive datetime
        ])

    # Save the workbook to a BytesIO object
    output = BytesIO()
    workbook.save(output)
    output.seek(0)  # Move to the beginning of the BytesIO object

    # Create an HTTP response with the xlsx file
    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=student_results.xlsx'  # Change to .xlsx
    
    return response


def download_student_result_xlsm(request, result_id):
    result = get_object_or_404(StudentResult, id=result_id)
    student_answers = StudentAnswer.objects.filter(
        account=result.account,
        question__assignment=result.assignment
    ).select_related('question')

    # Create a workbook and add a worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Detailed Results"

    # Add headers
    headers = ['Question', "Student's Answer", 'Correct Answer', 'Score']
    worksheet.append(headers)

    # Add data to the worksheet
    for answer in student_answers:
         options_mapping = {
            'Option1': answer.question.option1,
            'Option2': answer.question.option2,
            'Option3': answer.question.option3,
            'Option4': answer.question.option4,
        }
        
         worksheet.append([
            answer.question.question,
            options_mapping.get(answer.answer, answer.answer),  # Get actual option text
            options_mapping.get(answer.question.answer, answer.question.answer),  # Get actual option text
            answer.question.score if answer.answer == answer.question.answer else 0,
        ])

    # Save the workbook to a BytesIO object
    output = BytesIO()
    workbook.save(output)
    output.seek(0)  # Move to the beginning of the BytesIO object

    # Create an HTTP response with the xlsx file
    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={result.account.username}_results.xlsx'  # Use .xlsx for the content type
    
    return response
    
#publish assignment button
def publish_assignment(request, aid):
    assignment = get_object_or_404(Assignment, aid=aid)
    assignment.published = True
    assignment.save()
    return redirect('assignment_list')

#AI Create Question
def Ai_question_create(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        difficulty = request.POST.get('difficulty')
        num_questions = int(request.POST.get('num_questions', 1))
        
        # Set score based on difficulty
        score = {
            'easy': 5,
            'middle': 10,
            'hard': 15
        }.get(difficulty,)
        
        prompt = f"""Generate {num_questions} multiple choice questions about {topic} at {difficulty} difficulty level.

        Each question and its options must be under 255 characters.

        Return the response in this exact JSON array format:

        [
            {{

                "question": "question text", 

                "option1": "first option",

                "option2": "second option",

                "option3": "third option",
                "option4": "fourth option",

                "answer": "Option1",

                "score": {score},

                "level": "{difficulty}"
            }}
        ]
        Make sure the response is valid JSON and the answer field matches exactly one of: Option1, Option2, Option3, or Option4."""
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text.replace('```json', '').replace('```', '').strip()
            
            try:
                questions_data = json.loads(response_text)
                if isinstance(questions_data, dict):
                    questions_data = [questions_data]
                
                # Get unpublished assignments for the form
                assignments = Assignment.objects.filter(published=False)
                
                
                return render(request, 'AI_Q.html', {
                    'generated_questions': questions_data,
                    'assignments': assignments
                })
                
            except json.JSONDecodeError as je:
                return render(request, 'AI_Q.html', {
                    'error': f"Invalid JSON format in AI response. Please try again.",
                    'assignments': Assignment.objects.filter(published=False)
                })
            
        except Exception as e:
            return render(request, 'AI_Q.html', {
                'error': f"Error generating questions: {str(e)}",
                'assignments': Assignment.objects.filter(published=False)
            })
    
    return render(request, 'AI_Q.html', {
        'assignments': Assignment.objects.filter(published=False)
    })




def Ai_yes_no_create(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        difficulty = request.POST.get('difficulty')
        num_questions = int(request.POST.get('num_questions', 1))
        
        # Set score based on difficulty
        score = {
            'easy': 5,
            'middle': 10,
            'hard': 15
        }.get(difficulty, 5)
        
        prompt = f"""Generate {num_questions} Yes/No questions about {topic} at {difficulty} difficulty level.
        Each question and its options must be under 255 characters.
        Return the response in this exact JSON array format:
        [
            {{
                "question": "question text that can be answered with Yes or No",
                "answer": "Option1",
                "score": {score},
                "level": "{difficulty}"
            }}
        ]
        Make sure the response is valid JSON and the answer field is "Option1" for Yes or "Option2" for No.
        The questions should be clear and unambiguous with a definitive Yes or No answer."""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.replace('```json', '').replace('```', '').strip()
            
            try:
                questions_data = json.loads(response_text)
                if isinstance(questions_data, dict):
                    questions_data = [questions_data]
                
                # Get unpublished assignments for the form
                assignments = Assignment.objects.filter(published=False)
                
                
                return render(request, 'AI_yes_no.html', {
                    'generated_questions': questions_data,
                    'assignments': assignments
                })
                
            except json.JSONDecodeError as je:
                return render(request, 'AI_yes_no.html', {
                    'error': f"Invalid JSON format in AI response. Please try again.",
                    'assignments': Assignment.objects.filter(published=False)
                })
            
        except Exception as e:
            return render(request, 'AI_yes_no.html', {
                'error': f"Error generating questions: {str(e)}",
                'assignments': Assignment.objects.filter(published=False)
            })
    
    return render(request, 'AI_yes_no.html', {
        'assignments': Assignment.objects.filter(published=False)
    })
