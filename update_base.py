import os

filepath = 'c:/djangooo/templates/student_panel/base_student.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("{% url 'cart' %}", "{% url 'student_cart' %}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done updating base_student')
