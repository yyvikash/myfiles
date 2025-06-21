from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import File as DjangoFile
from django.conf import settings
from .models import tbl_files, tbl_users
from datetime import date
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader
import zipfile, os, io
import comtypes
import time
from comtypes.client import CreateObject
# Optional dependencies
try:
    from docx2pdf import convert as docx2pdf_convert
except ImportError:
    docx2pdf_convert = None

try:
    import comtypes.client
except ImportError:
    comtypes = None

try:
    from pdf2docx import Converter as PDF2DOCX_Converter
except ImportError:
    PDF2DOCX_Converter = None

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None


def conversion_type(request):
    if request.method == "POST":
        action = request.POST.get("action")
        uploaded_files = request.FILES.getlist("file")
        conversion_type = request.POST.get("conversion_type")

        if not uploaded_files or not conversion_type:
            return JsonResponse({"error": "Please select both file and conversion type."}, status=400)

        input_paths = []
        try:
            # Save uploaded files
            for f in uploaded_files:
                safe_name = os.path.basename(f.name)
                saved_path = default_storage.save(safe_name, f)
                input_paths.append(default_storage.path(saved_path))

            output_path = None
            converted_dir = os.path.join(settings.MEDIA_ROOT, "converted")
            os.makedirs(converted_dir, exist_ok=True)

            def build_output_path(file_obj, new_ext):
                base = os.path.splitext(os.path.basename(file_obj.name))[0]
                return os.path.join(converted_dir, f"{base}_converted.{new_ext}")

            if conversion_type == "jpg_to_png":
                with Image.open(input_paths[0]) as img:
                    output_path = build_output_path(uploaded_files[0], "png")
                    img.save(output_path, "PNG")

            elif conversion_type == "png_to_jpg":
                with Image.open(input_paths[0]) as img:
                    rgb_img = img.convert("RGB")
                    output_path = build_output_path(uploaded_files[0], "jpg")
                    rgb_img.save(output_path, "JPEG")

            elif conversion_type in ["jpg_to_pdf", "jpeg_to_pdf", "all_to_pdf"]:
                images = []
                for p in input_paths:
                    if p.lower().endswith((".jpg", ".jpeg", ".png")):
                        img = Image.open(p).convert("RGB")
                        images.append(img)
                if not images:
                    return JsonResponse({"error": "No valid image files to convert."}, status=400)
                output_path = build_output_path(uploaded_files[0], "pdf")
                images[0].save(output_path, save_all=True, append_images=images[1:])

            elif conversion_type == "pdf_to_jpg":
                if not convert_from_path:
                    return JsonResponse({"error": "Missing dependency: pdf2image"}, status=500)

                zip_buffer = io.BytesIO()
                saved_images = []

                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    pages = convert_from_path(input_paths[0])
                    for i, page in enumerate(pages):
                        img_name = f"{os.path.splitext(os.path.basename(input_paths[0]))[0]}_page_{i + 1}.jpg"
                        img_path = os.path.join(converted_dir, img_name)
                        page.save(img_path, "JPEG")
                        saved_images.append(img_path)
                        zip_file.write(img_path, img_name)

                zip_buffer.seek(0)

                if action == "convert_and_upload":
                    try:
                        user_email = request.session.get("email")
                        user = tbl_users.objects.get(Email=user_email)

                        # Save ZIP to disk temporarily
                        zip_filename = f"{os.path.splitext(os.path.basename(input_paths[0]))[0]}_pages.zip"
                        zip_path = os.path.join(converted_dir, zip_filename)
                        with open(zip_path, "wb") as f:
                            f.write(zip_buffer.getvalue())

                        with open(zip_path, "rb") as zip_file:
                            django_file = DjangoFile(zip_file, name=zip_filename)
                            tbl_files.objects.create(
                                Email=user,
                                File=django_file,
                                File_Name=zip_filename,
                                Upload_Date=date.today(),
                                Description="All PDF pages converted to JPG (ZIP)",
                                File_Type="zip"
                            )

                        if os.path.exists(zip_path):
                            os.remove(zip_path)

                    except Exception as db_err:
                        return JsonResponse({"error": f"Upload failed: {str(db_err)}"}, status=500)

                # Cleanup temporary JPGs
                for img_path in saved_images:
                    if os.path.exists(img_path):
                        os.remove(img_path)

                return HttpResponse(
                    zip_buffer.read(),
                    content_type='application/zip',
                    headers={'Content-Disposition': 'attachment; filename="pdf_pages_converted.zip"'}
                )

            elif conversion_type == "jpeg_to_png":
                with Image.open(input_paths[0]) as img:
                    output_path = build_output_path(uploaded_files[0], "png")
                    img.save(output_path, "PNG")

            elif conversion_type == "split_pdf":
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    reader = PdfReader(input_paths[0])
                    for i in range(len(reader.pages)):
                        page_output_path = os.path.join(converted_dir, f"page_{i+1}.pdf")
                        merger = PdfMerger()
                        merger.append(input_paths[0], pages=(i, i + 1))
                        with open(page_output_path, "wb") as out_f:
                            merger.write(out_f)
                        merger.close()
                        zip_file.write(page_output_path, os.path.basename(page_output_path))
                        os.remove(page_output_path)
                zip_buffer.seek(0)
                return HttpResponse(
                    zip_buffer.read(),
                    content_type='application/zip',
                    headers={'Content-Disposition': 'attachment; filename="split_pages.zip"'}
                )

            elif conversion_type == "merge_pdf":
                merger = PdfMerger()
                for p in input_paths:
                    merger.append(p)
                output_path = build_output_path(uploaded_files[0], "pdf")
                with open(output_path, "wb") as out_f:
                    merger.write(out_f)
                merger.close()

            elif conversion_type == "compress":
                output_path = build_output_path(uploaded_files[0], "zip")
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(input_paths[0], os.path.basename(input_paths[0]))

            elif conversion_type == "docx_to_pdf":
                if not docx2pdf_convert:
                    return JsonResponse({"error": "Missing dependency: docx2pdf"}, status=500)
                output_path = build_output_path(uploaded_files[0], "pdf")
                docx2pdf_convert(input_paths[0], output_path)

            # elif conversion_type == "pptx_to_pdf":
            #     if not comtypes:
            #         return JsonResponse({"error": "Missing dependency: comtypes"}, status=500)

            #     import time
            #     from comtypes.client import CreateObject

            #     comtypes.CoInitialize()
            #     try:
            #         powerpoint = CreateObject("Powerpoint.Application", dynamic=True)
            #         powerpoint.Visible = 1
            #         time.sleep(2)  # Wait for PowerPoint to fully initialize

            #         ppt_path = os.path.abspath(input_paths[0]).replace("/", "\\")
            #         ppt = powerpoint.Presentations.Open(ppt_path)
            #         print("Opening PowerPoint file at:", ppt_path)

            #         output_path = build_output_path(uploaded_files[0], "pdf")
            #         ppt.SaveAs(output_path, 32)  # 32 = PDF format
            #         ppt.Close()
            #         powerpoint.Quit()
            #     finally:
            #         comtypes.CoUninitialize()

            elif conversion_type == "pdf_to_docx":
                if not PDF2DOCX_Converter:
                    return JsonResponse({"error": "Missing dependency: pdf2docx"}, status=500)
                output_path = build_output_path(uploaded_files[0], "docx")
                cv = PDF2DOCX_Converter(input_paths[0])
                cv.convert(output_path, start=0, end=None)
                cv.close()

            else:
                return JsonResponse({"error": "Unsupported conversion type or missing library."}, status=400)

            with open(output_path, "rb") as f:
                file_data = f.read()

            if action == "convert_and_upload" and output_path and os.path.exists(output_path):
                try:
                    user_email = request.session.get("email")
                    user = tbl_users.objects.get(Email=user_email)
                    with open(output_path, "rb") as f_out:
                        clean_name = os.path.basename(output_path)
                        django_file = DjangoFile(f_out, name=clean_name)
                        tbl_files.objects.create(
                            Email=user,
                            File=django_file,
                            File_Name=clean_name,
                            Upload_Date=date.today(),
                            Description=f"Converted using {conversion_type}",
                            File_Type=os.path.splitext(clean_name)[1].lstrip('.')
                        )
                except Exception as db_err:
                    return JsonResponse({"error": f"Upload failed: {str(db_err)}"}, status=500)

            return HttpResponse(
                file_data,
                content_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{os.path.basename(output_path)}"'}
            )

        except Exception as e:
            return JsonResponse({"error": f"Internal Error: {str(e)}"}, status=500)

        finally:
            for p in input_paths:
                if os.path.exists(p):
                    os.remove(p)
            if 'output_path' in locals() and output_path and os.path.exists(output_path) and action != "convert_and_upload":
                os.remove(output_path)

    return render(request, "conversion_type.html")



def upload_file(request):
    if not request.session.get("email"):
        return HttpResponse("<script>alert('Please login to your account');window.location.href='/login/';</script>")

    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        if file.size <= 30 * 1024 * 1024:  # 30MB
            user_email = request.session.get('email')
            user = tbl_users.objects.get(Email=user_email)

            file_name = file.name
            file_type = os.path.splitext(file_name)[1][1:].upper()  # e.g., 'PDF'

            tbl_files.objects.create(
                Email=user,
                File=file,
                Upload_Date=date.today(),
                File_Name=file_name,
                File_Type=file_type,
                Description=request.POST.get('description', '')
            )
            request.session['upload_success'] = True
        else:
            request.session['upload_success'] = False

    request.session.modified = True
    return redirect('dashboard')

