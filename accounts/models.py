from django.db import models

# Create your models here.
class Account(models.Model):
    Area_Level = (
        (0, 'student'),
        (1, 'lecturer')
    )
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=225, null=False, verbose_name="username")
    email = models.EmailField(max_length=50, null=False, verbose_name="email")
    password = models.CharField(max_length=512, null=False, verbose_name="password")
    customer_type = models.IntegerField(default=0, choices=Area_Level, verbose_name="customer_type")

class Assignment(models.Model):
    mechanism_Level = (
        (0, 'random'),
        (1, 'fixed'),
        (2, 'dynamic'),
    )
    aid = models.AutoField(primary_key=True)
    assignment_name = models.CharField(max_length=255)
    mechanism_type = models.IntegerField(default=0, choices=mechanism_Level, verbose_name="customer_type")
    published = models.BooleanField(default=False)

    def __str__(self):
        return "%s" %(self.assignment_name)
    
    class Meta:
        db_table="Assignment"

class Questionbank(models.Model):
    assignment = models.ForeignKey(Assignment,on_delete=models.CASCADE, default=1)
    qid = models.AutoField(primary_key=True)
    question = models.CharField(max_length=255)
    option1 = models.CharField(max_length=255, null=True, blank=True)  # Allow null
    option2 = models.CharField(max_length=255, null=True, blank=True)  
    option3 = models.CharField(max_length=255, null=True, blank=True) 
    option4 = models.CharField(max_length=255, null=True, blank=True)  
    cat=(('Option1','Option1'),('Option2','Option2'),('Option3','Option3'),('Option4','Option4'))
    answer=models.CharField(max_length=200,choices=cat)
    level = models.CharField(max_length=10, choices=(('easy', 'easy'), ('middle', 'middle'), ('hard', 'hard')))
    score = models.IntegerField()

    def __str__(self):
        return "<%s:%S>" %(self.assignment,self.question) 
    
    class Meta:
        db_table="Questionbank"

class StudentAnswer(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    question = models.ForeignKey(Questionbank, on_delete=models.CASCADE)
    answer = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return "<%s:%S>" %(self.account,self.question) 
    
    class Meta:
        db_table="StudentAnswer"

class StudentResult(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    total_marks = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "<%s:%S>" %(self.account,self.assignment,self.total_marks) 
    
    class Meta:
        db_table="StudentResult"

