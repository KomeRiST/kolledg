from django.shortcuts import render_to_response, render, Http404
from . import models, forms, settings
from datetime import *
from django.contrib import auth
from django.db.models import Sum
from django.forms.formsets import formset_factory, BaseFormSet
from django.db import connection
from django.http import HttpResponse
from win32com import client
import os
import pythoncom
from django.core.serializers import serialize


def excel(request, group_id): # Экспорт учебного плана в файл Excel
    # Получаем инфу по группе.
    group = models.Groups.objects.get(pk=group_id)
    max_sem = group.max_sem()
    uch_plan = [] # массив дисциплин уч. плана
    # Получаем учебный план по группе.
    discip = models.GroupDisc.objects.filter(id_group=group_id)
    for d in discip:
        # Получаем нагрузку по дисциплине.
        nagryz = models.GroupDiscNagruzka.objects.filter(id_disc=d)
        item = {'index': d.disc_index, 'disc': d.disciplina, 'max': d.max_nagruzka,
                'sam': d.samostoyatelnaya_raboa, 'vsego': d.vsego_zanyatii, 'lekcii': d.lekcii,
                'prak': d.praktic, 'kurs_pod': d.kurs_podgotovka, 'nagruzka': nagryz}
        uch_plan.append(item)
    # Создаем COM объект
    pythoncom.CoInitialize()
    Excel = client.Dispatch("Excel.Application")
    Excel.DisplayAlerts = False
    # Формируем путь к файлу для экспорта
    p = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '\\media\\export\\uch_plan\\'
    pp = p + str(group.max_sem()) + '_sem.xlsx'
    # Открываем книгу
    wb = Excel.Workbooks.Open(pp)
    # Получаем доступ к активному листу
    sheet = wb.ActiveSheet
    c = 6 # С какой строки начинать читать лист книги
    for i in uch_plan:
        # Получаем ячейки для записи
        sheet.Rows("{}:{}".format(c, c)).Insert(-4121, 0)
        # Записываем данные в ячецки
        sheet.Cells(c, 1).value = i['index']
        sheet.Cells(c, 2).value = i['disc']
        for x in i['nagruzka']:
            sheet.Cells(c, 2 + x.semestr).value = x.forma_attestacii
            sheet.Cells(c, 8 + max_sem + x.semestr).value = x.chasov
        sheet.Cells(c, 3 + max_sem).value = i['max']
        sheet.Cells(c, 4 + max_sem).value = i['sam']
        sheet.Cells(c, 5 + max_sem).value = i['vsego']
        sheet.Cells(c, 6 + max_sem).value = i['lekcii']
        sheet.Cells(c, 7 + max_sem).value = i['prak']
        sheet.Cells(c, 8 + max_sem).value = i['kurs_pod']
        c += 1
    # Сохраним файл
    wb.SaveAs(p + 'export.xlsx')
    # Закроем файл
    wb.Close()
    # Закроем COM объект
    Excel.Quit()

    response = HttpResponse(open(p + 'export.xlsx', 'rb').read())
    response['Redirect'] = '/'
    response['Content-Type'] = 'mimetype/submimetype'
    response['Content-Disposition'] = 'attachment; filename=' + group_id + ' uchebnyi plan.xlsx'
    return response


def read_sheets_import_excel(file_name): # Получаем список листов книги файла
    # Создаем COM объект
    pythoncom.CoInitialize()
    Excel = client.Dispatch("Excel.Application")
    Excel.DisplayAlerts = False
    # Формируем путь к файлу
    p = settings.MEDIA_ROOT + '\\import\\xls\\' + file_name
    # Открываем книгу
    wb = Excel.Workbooks.Open(p)
    # Получаем доступ к листам
    sh_col = wb.Worksheets.Count
    i = 1
    sh_names = [] # Массив названий листов книги
    while i <= sh_col:
        sh_names.append(wb.Worksheets(i).Name) # Добавляем название листа в массив
        i += 1
    # Закроем файл
    wb.Close()
    # Закроем COM объект
    Excel.Quit()
    return sh_names


def read_import_excel(file_name, sheet_name, sem):
    # Создаем COM объект
    pythoncom.CoInitialize()
    Excel = client.Dispatch("Excel.Application")
    Excel.DisplayAlerts = False
    # Формируем путь к файлу
    p = settings.MEDIA_ROOT + '\\import\\xls\\' + file_name
    # Открываем файл
    wb = Excel.Workbooks.Open(p)
    # Подсчитываем максимальное количество столбцов для чтения данных
    c = 8 + (sem * 2)
    # Получаем данные с листа
    sheet = wb.Worksheets(u'' + sheet_name).Range("A11:Z200")
    # Получаем последнюю строку с данными
    r = sheet.Cells.SpecialCells(11).Row
    # Таблица с инфой о предметах
    predmety = []
    i = 1
    # Цикл по строкам листа
    while i <= r:
        disc = [] # Массив данных дисциплины
        x = 1
        # Цикл по ячейкам строки
        while x <= c:
            stroka = str(sheet.Cells(i, x).Value)
            # Добавляем данные в дисциплину
            if stroka == 'None':
                disc.append('')
            else:
                disc.append(str(sheet.Cells(i, x).Value))
            x += 1
        # Добавляем дисциплину в в массив предметов
        predmety.append(disc)
        i += 1
    # Закроем файл
    wb.Close()
    # Закроем COM объект
    Excel.Quit()
    return predmety


def handle_uploaded_file(f, file_name): # Сохранение импортируемого файла на сервере
    with open(settings.MEDIA_ROOT + '\\import\\xls\\' + file_name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def import_excel(request, group_id): # Обработка импорта файла учебного плана (3-4 шага)
    user = auth.get_user(request)
    gr = models.Groups.objects.get(pk=group_id)
    if request.method == 'POST': # Если отправили данные на сервер ...
        if request.FILES is not None: #Шаг - 1. Передали файл
            form = forms.UploadFileForm(request.POST, request.FILES)
            if form.is_valid(): # Правильно ли передали файл?
                # Получаем файл
                newdoc = models.ImportFile(xlsfile=request.FILES['file'])
                # Узнаём его название
                file_name = newdoc.xlsfile.name
                # Сохраняем на сервере
                handle_uploaded_file(request.FILES['file'], file_name)
                page = 'kolledg/import_excel_uplan_step2.html'
                # Получаем список листов книги
                sh_names = read_sheets_import_excel(file_name)
                res = {'user': user, 'group': gr, 'file_name': file_name, 'sh_names': sh_names}

        if "select_sheet" in request.POST: # Шаг - 2. Выбрали лист для чтения уч. плана
            page = 'kolledg/import_excel_uplan_step3.html'
            infa = request.POST['select_sheet']
            html_table = 'kolledg/html_table/html_table_' + str(gr.max_sem()) + '.html'
            # Читаем данные с листа
            res = {'user': user, 'group': gr, 'sh_name': infa, 'html_table': html_table,
                   'predmety': read_import_excel(request.POST['up_file_name'],
                                                 request.POST['select_sheet'],
                                                 gr.max_sem())}
        if "form-TOTAL_FORMS" in request.POST: # Шаг - 3. Передали готовую таблицу с уч. планом
            page = 'kolledg/good_job.html'.format(group_id)
            res = {'user': user, 'group': gr}
            pst = {} # Для хранения ПОСТ запроса
            pst.update(request.POST)
            r = int(pst.pop('form-MAX_NUM_FORMS')[0])
            gr = models.Groups.objects.get(pk=group_id)
            ms = gr.max_sem()
            x = 0
            while x <= r:
                id_item = 'form-{}-{}'.format(x, 0)
                if id_item in pst:
                    print(pst['form-{}-{}'.format(x, 15)])
                    disc = models.GroupDisc()
                    disc.id_group = gr
                    id_item = 'form-{}-{}'.format(x, 0)
                    disc.disc_index = pst.pop(id_item)[0]
                    id_item = 'form-{}-{}'.format(x, 1)
                    disc.disciplina = pst.pop(id_item)[0]
                    id_item = 'form-{}-{}'.format(x, 2 + ms)
                    z = pst.pop(id_item)[0]
                    if z == '':
                        disc.max_nagruzka = 0
                    else:
                        disc.max_nagruzka = round(float(z))
                    id_item = 'form-{}-{}'.format(x, 3 + ms)
                    z = pst.pop(id_item)[0]
                    if z == '':
                        disc.samostoyatelnaya_raboa = 0
                    else:
                        disc.samostoyatelnaya_raboa = round(float(z))
                    id_item = 'form-{}-{}'.format(x, 4 + ms)
                    z = pst.pop(id_item)[0]
                    if z == '':
                        disc.vsego_zanyatii = 0
                    else:
                        disc.vsego_zanyatii = round(float(z))
                    id_item = 'form-{}-{}'.format(x, 5 + ms)
                    z = pst.pop(id_item)[0]
                    if z == '':
                        disc.lekcii = 0
                    else:
                        disc.lekcii = round(float(z))
                    id_item = 'form-{}-{}'.format(x, 6 + ms)
                    z = pst.pop(id_item)[0]
                    if z == '':
                        disc.praktic = 0
                    else:
                        disc.praktic = round(float(z))
                    id_item = 'form-{}-{}'.format(x, 7 + ms)
                    z = pst.pop(id_item)[0]
                    if z == '':
                        disc.kurs_podgotovka = 0
                    else:
                        disc.kurs_podgotovka = round(float(z))
                    disc.save()
                    y = 1
                    while y <= ms:
                        fa = pst.pop('form-{}-{}'.format(x, 1 + y))[0]
                        ch = pst.pop('form-{}-{}'.format(x, 7 + ms + y))[0]
                        if fa == '0':
                            fa = ''
                        if ch == '0':
                            ch = ''
                        if (fa == '') and (ch == ''):
                            y += 1
                        else:
                            nagruz = models.GroupDiscNagruzka()
                            nagruz.id_disc = disc
                            nagruz.semestr = y
                            nagruz.forma_attestacii = fa
                            ch = ch
                            if ch == '':
                                nagruz.chasov = 0
                            else:
                                nagruz.chasov = round(float(ch))
                            nagruz.save()
                            y += 1
                x += 1

    else: # Если GET запрос
        form = forms.UploadFileForm()
        page = 'kolledg/import_excel_uplan.html'
        res = {'user': user, 'group': gr, 'form': form}

    return render_to_response(page, res)


def sql_ne_attestacii(): # Получить все не аттестации (запрос в БД)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `prikaz_povtornaya_body` ORDER BY `shortname`, `disc`, `stud_fio` ASC ")
    rows = models.dictfetchall(cursor) # Преобразование QuerySet в Dictionary
    return rows


def sql_ocenki(group): # Получить все оценки студентов группы (запрос в БД)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `stud_ocenki` WHERE `id_group` = " + group)
    rows = models.dictfetchall(cursor) # Преобразование QuerySet в Dictionary
    return rows


# Формирование статистических данных для графиков на главной странице
def index(request):
    user = auth.get_user(request)
    gr = models.Groups.objects.filter(id__gt=0)
    sts = models.Stud2Group.objects.all()
    kc = models.Kompetencii.objects.filter(id__gt=0)

    def get_info(kurs, g):
        if kurs == 6:
            kurs = 0
            k = '6'
        else:
            k = str(kurs)
        cs = g.get_col_stud(kurs)
        data['d' + k][0] += g.get_col_beg(kurs)
        data['d' + k][1] += g.get_col_stud_dolg(kurs)[0]['col']
        data['d' + k][2] += cs
        if g.is_top58() == True:
            data['d' + k][3] += cs
        if g.is_top50() == True:
            data['d' + k][4] += cs
        data['d' + k][5] += 0

    data = {
        'd1': [0, 0, 0, 0, 0, 0],
        'd2': [0, 0, 0, 0, 0, 0],
        'd3': [0, 0, 0, 0, 0, 0],
        'd4': [0, 0, 0, 0, 0, 0],
        'd5': [0, 0, 0, 0, 0, 0],
        'd6': [0, 0, 0, 0, 0, 0],
    }
    for g in gr:
        get_info(1, g)
        get_info(2, g)
        get_info(3, g)
        get_info(4, g)
        get_info(5, g)
        get_info(6, g)

    def sum(x):
        r = 0
        for item in data:
            r += data[item][x]
        return str(r)

    categories = {'cat1': sum(0),
                  'cat2': sum(1),
                  'cat3': sum(2),
                  'cat4': sum(3),
                  'cat5': sum(4),
                  'cat6': sum(5)}
    g = {'groups': gr, 'studs': sts, 'kompitencii': kc, 'categories': categories, 'data': data, 'user': user,
         'index': 'class=active'}
    return render_to_response('index2.html', g)


def print_(request, tip):
    prepods = {}
    if tip == 'group':
        params = models.Groups.objects.filter(id__gt=0)
    if tip == 'list_dolgnikov':
        now = datetime.now()
        prepods = models.Prepods.objects.all()
        params = models.Dolg_iz_prikaza.objects.raw(
            "SELECT * FROM `dolgi_po_prikazam` WHERE `ocenka` = 0 AND `data_sdachi` <= %s", [now])
    if tip == 'list_dolgov':
        params = models.Groups.objects.filter(id__gt=0)
    res = {'tip': tip, 'data': params, 'dop_date': prepods}
    return render_to_response('kolledg/print.html', res)


def prikazy(request):
    user = auth.get_user(request)
    dvig_kontingent = models.PrikazStudZach.objects.values('id_prik__nomer', 'id_prik__datap',
                                                           'id_group__shortname').annotate(Sum('id_group')).order_by()
    prik_povtornaya = models.PrikazBegStud.objects.all().order_by('id_prik__datap')
    result = {'dvig_kontingent': dvig_kontingent, 'prik_povtornaya': prik_povtornaya, 'user': user,
              'prikazy': 'class=active'}
    return render_to_response('kolledg/prikazy.html', result)


def kolledg(request):
    return render_to_response('kolledg/index.html')


def group(request, group_id):
    user = auth.get_user(request)
    try:
        gr = models.Groups.objects.get(pk=group_id)
        html_table = 'kolledg/html_table/html_table_' + str(gr.max_sem()) + '.html'
        studs = models.Stud2Group.objects.filter(id_group=group_id).order_by("id_stud__studfam")
        predmets = models.GroupDisc.objects.filter(id_group=group_id)
        # ocenki = models.stud_ocenki.objects.raw("SELECT * FROM `stud_ocenki` WHERE `id_group` = %s ", [group_id])
        ocenki = sql_ocenki(group_id)
        print("Ocenki: ", ocenki)
        # ocenki = ocenki.export()
        # ocenki = serialize('json', ocenki)
        discipliny = serialize('json', predmets)
        discnagryz = serialize('json', models.GroupDiscNagruzka.objects.filter(id_disc__id_group=group_id))
    except models.Groups.DoesNotExist:
        raise Http404("Group does not exist")

    return render_to_response('kolledg/group_page_2.html',
                              {'maxSem': range(1, gr.max_sem() + 1), 'group': gr, 'studs': studs, 'user': user, 'predmets': predmets,
                               'discipliny': discipliny, 'discnagryz': discnagryz, 'html_table': html_table, 'ocenki': ocenki})


def save_up(request):
    pst = {}
    pst.update(request.POST)
    try:
        disc_form = forms.FormDiscGroup(request.POST)
        if disc_form.is_valid():
            m = models.GroupDisc.objects.get(pk=request.POST['id'])
            m.disciplina = disc_form.cleaned_data['disciplina']
            m.max_nagruzka = disc_form.cleaned_data['max_nagruzka']
            m.samostoyatelnaya_raboa = disc_form.cleaned_data['samostoyatelnaya_raboa']
            m.vsego_zanyatii = disc_form.cleaned_data['vsego_zanyatii']
            m.lekcii = disc_form.cleaned_data['lekcii']
            m.praktic = disc_form.cleaned_data['praktic']
            m.kurs_podgotovka = disc_form.cleaned_data['kurs_podgotovka']
            m.save()
            g = disc_form.cleaned_data['id_group']
            x = 1
            col = g.max_sem()
            while x <= col:
                id_nagruz = request.POST['id_nagruz-' + str(x)]
                forma_attestacii = request.POST['forma_attestacii-' + str(x)]
                chasov = request.POST['chasov-' + str(x)]
                if id_nagruz == '':
                    if len(forma_attestacii) > 0 or len(chasov) > 0:
                        n = models.GroupDiscNagruzka(id_disc=m, semestr=x, forma_attestacii=forma_attestacii,
                                                     chasov=chasov)
                        n.save()
                else:
                    n = models.GroupDiscNagruzka.objects.get(pk=id_nagruz)
                    n.forma_attestacii = forma_attestacii
                    n.chasov = chasov
                    n.save()
                x += 1
    except:
        raise Http404("Ошибка сохранения учебного плана!!!")
    return HttpResponse({'name': 'name', 'phonenumber': 'phonenumber'})


def get_stud(request, stud_id):
    user = auth.get_user(request)
    stud = models.Students.objects.filter(pk=stud_id)
    result = {'tip': 'stud', 'stud': stud, 'user': user}
    return render_to_response('test.html', result)


def prikaz(request, tip):
    user = auth.get_user(request)
    if tip == 'zachislenie':
        res = models.PrikazStudZach.objects.values('id_prik__id', 'id_prik__nomer', 'id_prik__datap',
                                                   'id_group__shortname').annotate(Sum('id_group')).order_by(
            '-id_prik__datap')
    if tip == 'perevod':
        res = models.Perevod.objects.values('id_prik__id', 'id_prik__nomer', 'id_stud', 'id_prik__datap',
                                            'id_group_from__shortname', 'id_group_in__shortname').annotate(
            Sum('id_stud')).order_by('-id_prik__datap')
    if tip == 'otchislenie':
        res = {}
    result = {'tip': tip, 'data': res, 'user': user}
    return render_to_response('test.html', result)


def prik(request, tip, prik_id):
    user = auth.get_user(request)
    if tip == 'zachislenie_':
        res = models.PrikazStudZach.objects.filter(id_prik=prik_id).order_by('id_group')
    if tip == 'perevod_':
        res = models.Perevod.objects.filter(id_prik=prik_id).order_by('id_stud__studfam')
    if tip == 'otchislenie_':
        res = {}
    result = {'tip': tip, 'data': res, 'user': user}
    return render_to_response('test.html', result)


def new_prikaz(request):
    user = auth.get_user(request)
    class RequiredFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            super(RequiredFormSet, self).__init__(*args, **kwargs)
            for form in self.forms:
                form.empty_permitted = False

    StudsFormSet = formset_factory(forms.Student, max_num=25)
    prikaz_form = forms.TestForm(request.POST)
    if prikaz_form.is_valid():
        pst = {}
        pst.update(request.POST)
        n = pst.pop('nomer')[0]
        dp = pst.pop('datap')[0]
        try:
            getPrikaz = models.Prikazy.objects.get(nomer=n, datap=dp)
            prik = getPrikaz
        except:
            prik = prikaz_form.save()
        col_forms = int(pst.pop('form-TOTAL_FORMS')[0])
        x = 0
        print(pst)
        while x < col_forms:
            f = pst.pop('form-' + str(x) + '-Fam')[0]
            n = pst.pop('form-' + str(x) + '-name')[0]
            o = pst.pop('form-' + str(x) + '-otch')[0]
            b = pst.pop('form-' + str(x) + '-birsday')[0]
            a = pst.pop('form-' + str(x) + '-adress')[0]
            if b == '':
                b = '1900-01-01'
            todo_item = models.Students(name=n, otch=o, birsday=b, adress=a)
            todo_item.save()
            studfam = models.StudFam(id_stud=todo_item, data_izm=b, fam=f)
            studfam.save()
            g = pst.pop('form-' + str(x) + '-Group')[0]
            g = models.Groups.objects.get(id=g)
            sg = models.Stud2Group(id_stud=todo_item, id_group=g)
            sg.save()
            pz = models.PrikazStudZach(id_group=g, id_stud=todo_item, id_prik=prik)
            pz.save()
            x += 1
        result = {'user': user}
        page = 'kolledg/good_job.html'
    else:
        prikaz_form = forms.TestForm()
        studs_formset = StudsFormSet()
        result = {'todo_list_form': prikaz_form,
                  'todo_item_formset': studs_formset,
                  'user': user}
        page = 'prikaz_new_2.html'
    return render_to_response(page, result)


def prikaz_new_perevod(request):
    user = auth.get_user(request)

    class RequiredFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            super(RequiredFormSet, self).__init__(*args, **kwargs)
            for form in self.forms:
                form.empty_permitted = False

    StudsFormSet = formset_factory(forms.FormPrikPerevodStuds, max_num=25)
    prikaz_form = forms.TestForm(request.POST)
    if prikaz_form.is_valid():
        pst = {}
        pst.update(request.POST)
        result = {'user': user}
    else:
        prikaz_form = forms.TestForm()
        studs_formset = StudsFormSet()
        result = {'user': user, 'todo_list_form': prikaz_form, 'todo_item_formset': studs_formset}
    return render_to_response('kolledg/prikaz_new_perevod.html', result)


def prikaz_povtornaya(request):
    user = auth.get_user(request)
    prikaz_form = forms.FormNewPrikPovtornaya()
    if request.method == "POST":
        pst = {}
        pst.update(request.POST)
        n = pst.pop('nomer')[0]
        dp = pst.pop('datap')[0]
        dp = datetime.strptime(dp, "%d.%m.%Y")
        dp = dp.strftime("%Y-%m-%d")
        srok = pst.pop('Srok')[0]
        srok = datetime.strptime(srok, "%d.%m.%Y")
        srok = srok.strftime("%Y-%m-%d")
        getPrikaz = models.Prikazy.objects.filter(nomer=n, datap=dp)
        if getPrikaz:
            prik = getPrikaz[0]
        else:
            prik = models.Prikazy.objects.create(nomer=n, datap=dp)
            prik.save()
            prik_srok = models.PrikazySroki.objects.create(id_prik=prik, date_end=srok)
            prik_srok.save()
        col_forms = int(pst.pop('form-TOTAL_FORMS')[0])
        x = 0
        while x < col_forms:
            print(x)
            if 'form-' + str(x) + '-DELETE' in pst:
                z = pst.pop('form-' + str(x) + '-DELETE')[0]
            else:
                g = pst.pop('form-' + str(x) + '-Group')[0]
                g = models.Groups.objects.get(id=g)
                s = pst.pop('form-' + str(x) + '-Stud')[0]
                s = models.Students.objects.get(id=s)
                n = pst.pop('form-' + str(x) + '-Nagruzka')[0]
                if n == 'None':
                    n = pst.pop('form-' + str(x) + '-id_disc_prik_beg')[0]
                n = models.GroupDiscNagruzka.objects.get(id=n)
                pz = models.PrikazBegStud(id_disc_nagruz=n, id_stud=s, id_prik=prik, ocenka=0, data_sdachi='2000-01-01')
                pz.save()
                if 'form-' + str(x) + '-id_prep' in pst:
                    pd = pst.pop('form-' + str(x) + '-id_prep')[0]
                else:
                    pd = pst.pop('form-' + str(x) + '-id_prep_prik_beg')[0]
                pd = models.Prepods.objects.get(id=pd)
                pbsp = models.PrikazBegStudPrep(id_beg=pz, kod=1, id_prep=pd)
                pbsp.save()
            x = x + 1
        result = {'user': user}
        return render_to_response('kolledg/good_job.html', result)
    else:
        rows = sql_ne_attestacii()
        e = len(rows)
        BodyPrikFormSet = formset_factory(forms.FormNewPrikPovtornayaBody, can_delete=True)
        formset = BodyPrikFormSet(initial=rows)
        result = {'todo_list_form': prikaz_form, 'prik_body': formset, 'user': user, 'col_items': e}
        return render_to_response('kolledg/prikaz_povtornaya.html', result)


def export_uch_plan(request, group_id):
    up = models.uch_plan.objects.raw(
        'SELECT *  FROM `uchebnyi_plan` WHERE (`id_disc` > 0) AND (`id_group` = ' + group_id + ') ORDER BY `semestr` ASC')
    dataset = up.export()
    result = {'res': dataset}
    return render_to_response('index2.html', result)

def begunok_print(request, beg_id):
    user = auth.get_user(request)
    begunok = models.PrikazBegStud.objects.get(pk=beg_id)
    try:
        prep = models.PrikazBegStudPrep.objects.get(id_beg=begunok)
        prep = prep.id_prep
    except:
        prep = ''
    res = {'fa': begunok.id_disc_nagruz.forma_attestacii,
           'prik': begunok.id_prik,
           'stud': begunok.id_stud,
           'group': begunok.id_disc_nagruz.id_disc.id_group,
           'disc':  begunok.id_disc_nagruz,
           'prik_date': '(пусто)',
           'prep': prep,
           'kom1': '(пусто)',
           'kom2': '(пусто)'}
    return render_to_response('kolledg/print_files_html/begunok.html', {'begunok': res, 'user': user})

def begunok_set(request, beg_id):
    user = auth.get_user(request)
    begunok = models.PrikazBegStud.objects.get(pk=beg_id)
    if request.method == 'POST':
        pst = {}
        pst.update(request.POST)
        form = forms.FormPrikBegStuds(request.POST)
        ocenka = pst.pop('ocenka')[0]
        data_sdachi = pst.pop('data_sdachi')[0]
        data_sdachi = datetime.strptime(data_sdachi, "%d.%m.%Y")
        data_sdachi = data_sdachi.strftime("%Y-%m-%d")
        if form.is_valid():
            begunok.ocenka = ocenka
            begunok.data_sdachi = data_sdachi
            begunok.save()
        psge = 'kolledg/good_job.html'
    else:
        form = forms.FormPrikBegStuds({'data_sdachi': begunok.data_sdachi, 'ocenka': begunok.ocenka})
        psge = 'kolledg/beg_change.html'
    res = {'form': form, 'begunok': begunok, 'user': user}
    return render_to_response(psge, res)

def vedomost_get(request, disc_id):
    user = auth.get_user(request)
    disc = models.GroupDiscNagruzka.objects.get(pk=disc_id)
    ved = models.Vedomosty.objects.filter(id_disc=disc_id)
    if len(ved) != 0:
        gr = ved[0].id_disc.id_disc.id_group
        studs = models.Stud2Group.objects.filter(id_group=gr)
        prepods = models.VedAttKom.objects.filter(id_ved=ved)
        res = {'vedomosty': ved, 'group': gr, 'studs': studs, 'user': user, 'prepods': prepods, 'disc': disc}
        return render_to_response('kolledg/vedomosty.html', res)
    else:
        return new_vedomost(request, disc_id)

def new_vedomost(request, disc_id):
    user = auth.get_user(request)
    disc = models.GroupDiscNagruzka.objects.get(id=disc_id)
    form = forms.FormNewVedomost
    form_prep = formset_factory(forms.FormNewVedAttKom, max_num=4, extra=1)
    res = {'user': user, 'form': form, 'form_prep': form_prep}
    if request.method == 'POST':
        pst = {}
        pst.update(request.POST)
        form = forms.FormNewVedomost(request.POST)
        form_prep = formset_factory(forms.FormNewVedAttKom)
        form_prep = form_prep(request.POST)
        data_zacheta = pst.pop('data_zacheta')[0]
        data_zacheta = datetime.strptime(data_zacheta, "%d.%m.%Y")
        data_zacheta = data_zacheta.strftime("%Y-%m-%d")
        nomer = pst.pop('nomer')[0]
        if form.is_valid() and form_prep.is_valid():
            ved = models.Vedomosty(id_disc=disc, nomer=nomer, data_zacheta=data_zacheta, data_vozvrata='2000-01-01')
            ved.save()
            for item_form in form_prep:
                if item_form.is_valid():
                    ved_att = models.VedAttKom(id_ved=ved, kod=item_form.cleaned_data['kod'], id_prep=item_form.cleaned_data['id_prep'])
                    ved_att.save()
                    studs = models.Stud2Group.objects.filter(id_group=ved.id_disc.id_disc.id_group)
            for st in studs:
                ved_st = models.VedomostOcenki(id_ved=ved, id_stud=st.id_stud, ocenka=0)
                ved_st.save()
        vedomost_get(request, disc_id)
    return render_to_response('kolledg/new_vedomost.html', res)

def studs_ved(request, tip, ved_id):
    user = auth.get_user(request)
    ved = models.Vedomosty.objects.get(pk=ved_id)
    studs = models.VedomostOcenki.objects.filter(id_ved=ved)
    AttKom = models.VedAttKom.objects.filter(id_ved=ved)
    col_stud = len(studs)
    x = 0
    y = 0
    for stud in studs:
        if stud.ocenka > 2:
            x += 1
            if stud.ocenka > 3:
                y += 1
    otnosit = int(x * 100 / col_stud)
    kach = int(y * 100 / col_stud)
    res = {'tip': tip, 'user': user, 'ved': ved, 'studs': studs, 'attkom': AttKom, 'otnosit': otnosit, 'kach': kach}
    return render_to_response('test.html', res)

def prepod_info(request, prepod_id):
    user = auth.get_user(request)
    prepod = models.Prepods.objects.get(id=prepod_id)
    res = {'prepod': prepod, 'user': user}
    return render_to_response('kolledg/prepod_info.html', res)