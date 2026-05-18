import os
import re

count = 0
for root, _, files in os.walk('e:/New folder/frontend/src/views'):
    for f in files:
        if f.endswith('.vue'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = re.sub(r'<div class="table-responsive"><table class="data-table" v-if="([^"]+)">',
                                 r'<div class="table-responsive" v-if="\1"><table class="data-table">',
                                 content)
                                 
            new_content = re.sub(r'<div class="table-responsive"><table v-if="([^"]+)" class="data-table">',
                                 r'<div class="table-responsive" v-if="\1"><table class="data-table">',
                                 new_content)

            if new_content != content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                count += 1
                print(f"Fixed {f}")
print(f"Total fixed: {count}")
