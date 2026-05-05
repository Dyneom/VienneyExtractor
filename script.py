import fitz  # pip install pymupdf
import re
import os


dir_source = "." # A COMPLETER
dir_sortie = "." # A COMPLETER

def extract_boxes_to_pdf(
    input_path,
    output_path,
    page_width=595,   # A4 (in pt)
    page_height=842,  # idem
    margin=40,        # space between boxes and page edges
    spacing=10,       # vertical gap between boxes
    min_width=100,
    min_height=20,
    ):
    source = fitz.open(input_path)
    output = fitz.open()
    elements = [r'(Proposition \d+.\d+)',r'(Définition \d+.\d+)',r'(Corollaire \d+.\d+)',r'(Théorème \d+.\d+)',r'(Lemme \d+.\d+)',r'Proposition-définition']
    current_page = None
    cursor_y = margin  # current vertical position on the page

    def new_page():
        nonlocal current_page, cursor_y
        current_page = output.new_page(width=page_width, height=page_height)
        cursor_y = margin

    new_page()  # first page   

    # get the title
    
    rect = fitz.Rect(0,0,600,170)

    temp = fitz.open()
    temp.insert_pdf(source, from_page=0, to_page=0)
    temp_page = temp[0]
    page_rect = temp_page.rect


    words = temp_page.get_text("blocks")  # (x0, y0, x1, y1, word, block_no, line_no, word_no)

    for word in words:
        word_rect = fitz.Rect(word[:4])
        if not rect.contains(word_rect):
            temp_page.add_redact_annot(word_rect)

    temp_page.apply_redactions()    



    box_h = rect.height
    box_w = min(rect.width, page_width - 2 * margin) 
    dest = fitz.Rect(0, cursor_y, margin + box_w, cursor_y + box_h)
    current_page.show_pdf_page(dest, temp, 0, clip=rect)
    cursor_y += box_h + spacing  # move cursor down

    temp.close()
    
    for i in range(len(source)):
        print("-",end="")
    print("]",end="",flush=True)
    
    for page_num in range(len(source)):  
             
        print("\b"*(len(source)+1),end="")

        for i in range(len(source)):
            if i < page_num:
                print("X",end="")
            else:
                print("-",end="")
        print("]",end="",flush=True)
        
        
        page = source[page_num]
        original_cropbox = page.cropbox
        drawings = page.get_drawings()
        found_objects = []
        
        for d in drawings:
            rect = d["rect"]
            if rect.width < 300 or rect.height < min_height:
                continue

            text = page.get_text("text", clip=rect)        
            pos = False
            c = 0
            while not pos and len(elements)>c:
                pos = re.search(elements[c],text)
                c+=1

            if pos and pos.group(0) not in found_objects: # /!\ only prop def per page allowed
                rect.x0-=3
                rect.y0-=3                                
                found_objects.append(pos.group(0))

                
                temp = fitz.open()
                temp.insert_pdf(source, from_page=page_num, to_page=page_num)
                temp_page = temp[0]
                page_rect = temp_page.rect
                
                words = temp_page.get_text("words")  # (x0, y0, x1, y1, word, block_no, line_no, word_no)
                
                

                for word in words:
                    word_rect = fitz.Rect(word[:4])       

                    if not rect.contains(word_rect):
                        temp_page.add_redact_annot(word_rect)

                temp_page.apply_redactions()                
                temp_page.set_cropbox(rect)  # crop to box on the isolated copy

                
                
               
                
                
                box_h = rect.height
                box_w = min(rect.width, page_width - 2 * margin)  # cap 

                # If box doesn't fit on current page, start a new one
                if cursor_y + box_h > page_height - margin:
                    new_page()

                # position of the box on the output page
                
                dest = fitz.Rect(margin, cursor_y, margin + box_w, cursor_y + box_h)
                current_page.show_pdf_page(dest, temp, 0)

                cursor_y += box_h + spacing  # move cursor down
                
                temp.close()

    print("\b"*(len(source)+1),end="")

    for i in range(len(source)):
            print("X",end="")            
    print("]",end="",flush=True)

    output.save(output_path, garbage=4, deflate=True)
    print(f" ✅ {len(output)} pages made")
    source.close()
    output.close()

paths=os.listdir(dir_source)

for el in paths:
    if re.match(r'Chapitre\d+.pdf',el):
        print(el," [",sep="",end="",flush=True)
        extract_boxes_to_pdf(f"{dir_source}/{el}", f"{dir_sortie}/{el}")
        
        