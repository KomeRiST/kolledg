from django.db import models
from datetime import *
from django.db import connection
# from import_export import resources


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


class GroupDisc(models.Model):
    id_group = models.ForeignKey('Groups', models.DO_NOTHING, db_column='id_group')
    disc_index = models.CharField(max_length=15)
    disciplina = models.TextField()
    max_nagruzka = models.IntegerField()
    samostoyatelnaya_raboa = models.IntegerField()
    vsego_zanyatii = models.IntegerField()
    lekcii = models.IntegerField()
    praktic = models.IntegerField()
    kurs_podgotovka = models.IntegerField()

    def __str__(self):
        return self.disc_index + ' ' + self.disciplina

    def get_nagruzka(self):
        return GroupDiscNagruzka.objects.filter(id_disc=self.pk)

    class Meta:
        managed = False
        db_table = 'group_disc'


class GroupDiscNagruzka(models.Model):
    id_disc = models.ForeignKey(GroupDisc, models.DO_NOTHING, db_column='id_disc')
    semestr = models.IntegerField()
    forma_attestacii = models.CharField(max_length=5)
    chasov = models.IntegerField()

    def __str__(self):
        return self.id_disc.__str__()

    class Meta:
        managed = False
        db_table = 'group_disc_nagruzka'


class Dolg_iz_prikaza(models.Model):
    id_d = models.CharField(max_length=100)
    id_prik = models.ForeignKey('Prikazy', models.DO_NOTHING, db_column='id_prik')
    id_stud = models.ForeignKey('Students', models.DO_NOTHING, db_column='id_stud')
    id_disc_nagruz = models.ForeignKey('GroupDiscNagruzka', models.DO_NOTHING, db_column='id_disc_nagruz')
    ocenka = models.IntegerField()
    data_sdachi = models.DateField()
    nomer = models.CharField(max_length=100)
    datap = models.DateField()
    disc_index = models.CharField(max_length=100)
    disciplina = models.CharField(max_length=255)
    semestr = models.IntegerField()
    forma_attestacii = models.CharField(max_length=100)
    id_group = models.ForeignKey('Groups', models.DO_NOTHING, db_column='id_group')
    date_end = models.DateField()


class Groups(models.Model):
    id_kompetencii = models.ForeignKey('Kompetencii', models.DO_NOTHING, db_column='id_kompetencii', related_name="%(app_label)s_%(class)s_related")
    shortname = models.CharField(max_length=10)
    data_zapuska = models.DateField()
    vmestimost = models.IntegerField()
    bazovoe_obraz = models.CharField(max_length=100)
    forma_obucheniya = models.CharField(max_length=50)
    srok_god = models.IntegerField()
    srok_mes = models.IntegerField()
    kurator = models.ForeignKey('Prepods', models.DO_NOTHING, db_column='kurator')

    def __str__(self):
        return self.shortname

    def is_top50(self):
        x = self.id_kompetencii.top50_58
        r = (x == 1)
        return r

    def is_top58(self):
        x = self.id_kompetencii.top50_58
        r = (self.is_top50() or (x == 2))
        return r

    def tek_sem(self):
        now = datetime.now()
        string_date = str(self.data_zapuska)
        then = datetime(*[int(i) for i in string_date.split("-")])
        delta = now - then
        y = int(delta.days/365)
        m = int(delta.days/30)
        b = (m - (y * 12))
        if b < 4:
            if y == 0:
                sem = 1
            else:
                sem = 1+(y*2)
        else:
            if y == 0:
                sem = 2
            else:
                sem = 2+(y*2)
        s = str(sem)
        return sem

    def get_kurs(self):
        tk = self.tek_sem()
        if tk < 3:
            r = 1
        elif tk < 5:
            r = 2
        elif tk < 7:
            r = 3
        elif tk < 9:
            r = 4
        elif tk < 11:
            r = 5
        else:
            r = 0
        return r

    def max_sem(self):
        r = (self.srok_god * 2)
        if self.srok_mes > 4:
            r += 2
        else:
            r += 1
        return r

    def get_ocenki_0(self):
        dp = Dolg_iz_prikaza.objects.raw("SELECT * FROM `dolgi_po_prikazam` WHERE `ocenka` = 0 AND `id_group` = %s", [self.id])
        return dp

    def get_col_stud_dolg(self, kurs):
        r = []
        if self.get_kurs() == kurs:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(`id_stud`) as col FROM `dolgi_po_prikazam` WHERE `ocenka` = 0 AND `id_group` = "+str(self.id)+" GROUP BY `id_stud`")
            r = dictfetchall(cursor)
        if r == []:
            r = [{'col': 0}]
        return r

    def col_dolgov(self):
        pbs = len(self.get_ocenki_0())
        return pbs

    def get_col_beg(self, kurs):
        if self.get_kurs() == kurs:
            r = self.col_dolgov()
        else:
            r = 0
        return r

    def get_studs(self):
        return Stud2Group.objects.filter(id_group=self.id)

    def get_col_stud(self, kurs):
        if self.get_kurs() == kurs:
            r = len(Stud2Group.objects.filter(id_group=self.id))
        else:
            r = 0
        return r

    def getVedomosty(self):
        return Vedomosty.objects.filter(id_disc__id_disc__id_group=self.id)

    def detail(self):
        return self.id_kompetencii

    def uch_plan(self):
        cursor = connection.cursor()
        # cursor.execute("UPDATE bar SET foo = 1 WHERE baz = %s", [self.baz])
        cursor.execute("SELECT *  FROM `uchebnyi_plan` WHERE (`id_disc` > 0) AND (`id_group` = "+str(self.pk)+") ORDER BY `semestr` ASC")
        rows = dictfetchall(cursor)
        return rows

    class Meta:
        managed = False
        db_table = 'groups'


class Kompet2Group(models.Model):
    id_kompet = models.ForeignKey('Kompetencii', models.DO_NOTHING, db_column='id_kompet')
    id_group = models.ForeignKey(Groups, models.DO_NOTHING, db_column='id_group')

    class Meta:
        managed = False
        db_table = 'kompet2group'


class Kompetencii(models.Model):
    kod = models.CharField(max_length=10)
    naimenovanie = models.CharField(max_length=255)
    kvalifikaciya = models.CharField(max_length=255)
    rab_professii = models.CharField(max_length=255)
    uroven_podgotovki = models.CharField(max_length=255)
    top50_58 = models.IntegerField(max_length=1)

    def __str__(self):
        return '{} {}'.format(self.kod, self.naimenovanie)

    def groups(self):
        return Groups.objects.filter(id_kompetencii=self.id)

    def studs(self):
        return Stud2Group.objects.filter(id_group__id_kompetencii=self.id)

    class Meta:
        managed = False
        db_table = 'kompetencii'


class Perevod(models.Model):
    id_prik = models.ForeignKey('Prikazy', models.DO_NOTHING, db_column='id_prik')
    id_stud = models.ForeignKey('Students', models.DO_NOTHING, db_column='id_stud')
    id_group_from = models.ForeignKey(Groups, models.DO_NOTHING, db_column='id_group_from', related_name="id_group_from")  # Field name made lowercase.
    id_group_in = models.ForeignKey(Groups, models.DO_NOTHING, db_column='id_group_in', related_name="id_group_in")  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'perevod'


class PerevodDisc(models.Model):
    id_perevod = models.ForeignKey(Perevod, models.DO_NOTHING, db_column='id_perevod')
    id_disc_from = models.ForeignKey(GroupDiscNagruzka, models.DO_NOTHING, db_column='id_disc_from', related_name="id_disc_from")
    id_disc_in = models.ForeignKey(GroupDiscNagruzka, models.DO_NOTHING, db_column='id_disc_in', related_name="id_disc_in")

    class Meta:
        managed = False
        db_table = 'perevod_disc'


class PrepodFam(models.Model):
    id_prepod = models.ForeignKey('Prepods', models.DO_NOTHING, db_column='id_prepod')
    fam = models.CharField(max_length=50)
    data_izm = models.DateField()

    def __str__(self):
        return self.fam

    class Meta:
        managed = False
        db_table = 'prepod_fam'


class Prepods(models.Model):
    fam = models.ForeignKey(PrepodFam, models.DO_NOTHING, db_column='id_prepod_fam')
    name = models.CharField(max_length=50)
    otch = models.CharField(max_length=50)
    birsday = models.DateField()

    def __str__(self):
        now = datetime.now()
        fio = self.get_fio(now)
        return fio

    def get_fio(self, dt):
        pf = PrepodFam.objects.filter(id_prepod=self.id)
        pf = pf.filter(data_izm__lte=dt)
        pf = pf.order_by('-data_izm')[0]
        return pf.fam + ' ' + self.name + ' ' + self.otch

    def kurator(self):
        try:
            g = Groups.objects.get(kurator=self.id, id__gt=0)
        except:
            g = False
        return g

    def vedomosti(self):
        return VedAttKom.objects.filter(id_prep=self.id)

    def begunki(self):
        return PrikazBegStudPrep.objects.filter(id_prep=self.id)

    class Meta:
        ordering = ['fam__fam']
        managed = False
        db_table = 'prepods'


class Prikazy(models.Model):
    nomer = models.CharField(max_length=50)
    datap = models.DateField()

    def __str__(self):
        return '№ '+self.nomer+' от '+str(self.datap)

    class Meta:
        managed = False
        db_table = 'prikazy'


class PrikazBegStud(models.Model):
    id_prik = models.ForeignKey(Prikazy, models.DO_NOTHING, db_column='id_prik')
    id_stud = models.ForeignKey('Students', models.DO_NOTHING, db_column='id_stud')
    id_disc_nagruz = models.ForeignKey(GroupDiscNagruzka, models.DO_NOTHING, db_column='id_disc_nagruz')
    ocenka = models.IntegerField()
    data_sdachi = models.DateField()

    def __str__(self):
        return 'Бегунок на имя {} по дисциплине {} на основании приказа {}'.format(self.stud(), self.disc(), self.prikaz())

    def prikaz(self):
        return self.id_prik.__str__()

    def stud(self):
        return self.id_stud.__str__()

    def disc(self):
        return self.id_disc_nagruz.__str__()

    class Meta:
        ordering = ['-id_prik__datap']
        managed = False
        db_table = 'prikaz_beg_stud'


class PrikazBegStudPrep(models.Model):
    id_beg = models.ForeignKey(PrikazBegStud, models.DO_NOTHING, db_column='id_beg')
    kod = models.IntegerField()
    id_prep = models.ForeignKey(Prepods, models.DO_NOTHING, db_column='id_prep')

    class Meta:
        managed = False
        db_table = 'prikaz_beg_stud_prep'


class PrikazStudZach(models.Model):
    id_prik = models.ForeignKey('Prikazy', models.DO_NOTHING, db_column='id_prik')
    id_stud = models.ForeignKey('Students', models.DO_NOTHING, db_column='id_stud')
    id_group = models.ForeignKey(Groups, models.DO_NOTHING, db_column='id_group')

    class Meta:
        managed = False
        db_table = 'prikaz_stud_zach'



class PrikazySroki(models.Model):
    id_prik = models.ForeignKey(Prikazy, models.DO_NOTHING, db_column='id_prik')
    date_end = models.DateField()

    class Meta:
        managed = False
        db_table = 'prikazy_sroki'


class Reminder(models.Model):
    dt = models.DateField()
    text = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'reminder'


class Students(models.Model):
    name = models.CharField(max_length=50)
    otch = models.CharField(max_length=50)
    birsday = models.DateField()
    adress = models.CharField(max_length=255)

    def __str__(self):
        now = datetime.now()
        fio = self.get_fio(now)
        return fio

    def get_group(self):
        r = Stud2Group.objects.get(stud_id=self.id)
        return r.group_id

    def fam(self):
        r = self.get_fam(0)
        return r

    def get_fam(self, dt):
        sf = StudFam.objects.filter(id_stud=self.id)
        if sf.count() == 0:
            r = ''
        else:
            if dt == 0:
                now = datetime.now()
                sf = sf.filter(data_izm__lte=now)
            else:
                sf = sf.filter(data_izm__lte=dt)
            sf = sf.order_by('-data_izm')[0]
            r = sf.fam
        return r

    def get_fio(self, dt):
        f = self.get_fam(dt)
        return f + ' ' + self.name + ' ' + self.otch

    def short_fio(self):
        f = self.get_fam(datetime.now())
        return f + ' ' + self.name[0] + '. ' + self.otch[0] + '.'

    def is_dolgi(self):
        pbs = PrikazBegStud.objects.filter(id_stud=self.id)
        return pbs

    class Meta:
        ordering = ['studfam']
        managed = False
        db_table = 'students'


class Stud2Group(models.Model):
    id_group = models.ForeignKey(Groups, models.DO_NOTHING, db_column='id_group')
    id_stud = models.ForeignKey(Students, models.DO_NOTHING, db_column='id_stud')

    def stud(self):
        return self.id_stud

    def group(self):
        return self.id_group

    class Meta:
        ordering = ['id_stud__studfam']
        managed = False
        db_table = 'stud2group'


class StudFam(models.Model):
    id_stud = models.ForeignKey(Students, models.DO_NOTHING, db_column='id_stud')
    fam = models.CharField(max_length=50)
    data_izm = models.DateField()

    def __str__(self):
        return self.fam

    class Meta:
        managed = False
        db_table = 'stud_fam'


class VedAttKom(models.Model):
    id_ved = models.ForeignKey('Vedomosty', models.DO_NOTHING, db_column='id_ved')
    kod = models.IntegerField()
    id_prep = models.ForeignKey(Prepods, models.DO_NOTHING, db_column='id_prep')

    class Meta:
        managed = False
        db_table = 'ved_att_kom'


class VedomostOcenki(models.Model):
    id_ved = models.ForeignKey('Vedomosty', models.DO_NOTHING, db_column='id_ved')
    id_stud = models.ForeignKey(Students, models.DO_NOTHING, db_column='id_stud')
    ocenka = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'vedomost_ocenki'


class Vedomosty(models.Model):
    id_disc = models.ForeignKey(GroupDiscNagruzka, models.DO_NOTHING, db_column='id_disc')
    nomer = models.IntegerField()
    data_zacheta = models.DateField()
    data_vozvrata = models.DateField()

    def __str__(self):
        return '{} сем. {} № {} от {} (возврат: {})'.format(self.id_disc.semestr, self.id_disc, self.nomer, self.data_zacheta, self.data_vozvrata)

    class Meta:
        managed = False
        db_table = 'vedomosty'


class NewPrikPovtornaya(Prikazy):
    Srok = models.DateField()

    def save(self, *args, **kwargs):
        prik = Prikazy(nomer=self.nomer, datap=self.datap)
        prik = prik.save()
        prik_srok = PrikazySroki(id_prik=prik, date_end=self.Srok)
        prik_srok.save()
        super(NewPrikPovtornaya, self).save(*args, **kwargs)


class NewPrikPovtornayaBody(models.Model):
    id_group = models.CharField(max_length=255)
    id_stud = models.CharField(max_length=255)
    id_prep = models.ForeignKey(Prepods, models.DO_NOTHING)
    id_disc = models.CharField(max_length=255)
    shortname = models.CharField(max_length=255)
    stud_fio = models.CharField(max_length=255)
    disc = models.CharField(max_length=255)
    semestr = models.CharField(max_length=255)
    forma_attestacii = models.CharField(max_length=255)


class uch_plan(models.Model):
    id_group = models.CharField(max_length=255)
    id_disc = models.CharField(max_length=255)
    id_disc_sem = models.CharField(max_length=255)
    disc = models.CharField(max_length=255)
    max_nagruzka = models.CharField(max_length=255)
    vsego_zanyatii = models.CharField(max_length=255)
    semestr = models.CharField(max_length=255)
    chasov = models.CharField(max_length=255)
    forma_attestacii = models.CharField(max_length=255)


class stud_ocenki(models.Model):
    id_group = models.ForeignKey(Groups, models.DO_NOTHING, db_column='id_group')
    id_stud = models.ForeignKey(Students, models.DO_NOTHING, db_column='id_stud')
    id_disc_nagruz = models.ForeignKey(GroupDiscNagruzka, models.DO_NOTHING, db_column='id_disc')
    ocenka = models.IntegerField()


class ImportFile(models.Model):
    xlsfile = models.FileField(upload_to='import/xls')


# class UchPlanResource(resources.ModelResource):
#     class Meta:
#         model = uch_plan
