import os

filepath = 'c:/djangooo/templates/dashboard/menu_makanan.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('<a href="#" class="food-img-wrapper">', '<a href="{% url \'student_menu_detail\' 1 %}" class="food-img-wrapper">')
content = content.replace('<a href="#" class="food-name">', '<a href="{% url \'student_menu_detail\' 1 %}" class="food-name">')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced links successfully.")
