from django.forms import *
from .models import *


class Student(ModelForm):
    Group = ModelChoiceField(queryset=Groups.objects.filter(pk__gt=0))
    Fam = CharField(label=u'Фамилия', min_length=3, max_length=50)

    class Meta:
        model = Students
        fields = '__all__'


class TestStudForm(Form):
    Group = ModelChoiceField(queryset=Groups.objects.filter(pk__gt=0))
    Fam = CharField(label=u'Фамилия', min_length=3, max_length=50)
    Name = CharField(label=u'Имя', min_length=3, max_length=50)
    Otch = CharField(label=u'Отчество', min_length=3, max_length=50)
    Dr = DateField(label=u'Дата рождения')
    Adress = CharField(label=u'Фамилия', min_length=3, max_length=50)

    def __init__(self, *args, **kwargs):
        super(TestForm, self).__init__(*args, **kwargs)

    def save(self):
        stud = Students(name=self.fields['Name'], otch=self.fields['Otch'],
                        birsday=self.fields['Dr'], adress=self.fields['Adress'])
        stud.save()
        studfam = StudFam(id_stud=stud.id, data_izm=stud.birsday, fam=self.Fam)
        studfam.save()


class TestForm(ModelForm):
    class Meta:
        model = Prikazy
        fields = '__all__'
        labels = {'nomer': u'Номер приказа',
                  'datap': u'Дата приказа'}

    def __init__(self, *args, **kwargs):
        super(TestForm, self).__init__(*args, **kwargs)


class FormNewPrikPovtornaya(ModelForm):
    class Meta:
        model = NewPrikPovtornaya
        fields = '__all__'
        labels = {'nomer': u'Номер приказа',
                  'datap': u'Дата приказа',
                  'Srok': u'Конечная дата действия приказа'}


class FormPrikPerevodStuds(ModelForm):
    class Meta:
        model = Perevod
        fields = '__all__'


class FormPrikBegStuds(ModelForm):
    class Meta:
        model = PrikazBegStud
        # fields = '__all__'
        fields = 'data_sdachi', 'ocenka'
        labels = {'ocenka': u'Оценка', 'data_sdachi': u'Дата сдачи'}


class FormDiscGroup(ModelForm):
    class Meta:
        model = GroupDisc
        fields = '__all__'


class FormNewPrikPovtornayaBody(ModelForm):
    class Meta:
        model = NewPrikPovtornayaBody
        fields = '__all__'


class FormNewVedAttKom(ModelForm):
    class Meta:
        model = VedAttKom
        fields = 'kod', 'id_prep'
        labels = {'kod': u'Код: 1-аттестующий; 2-комиссия', 'id_prep': u'Преподаватель'}


class FormNewVedomost(ModelForm):
    class Meta:
        model = Vedomosty
        fields = 'nomer', 'data_zacheta'
        labels = {'nomer': u'Номер по журналу выдачи ведомостей', 'data_zacheta': u'Дата проведения аттестации'}


class UploadFileForm(forms.Form):
    file = forms.FileField(label=u'Выберите файл для загрузки')