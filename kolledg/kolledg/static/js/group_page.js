    $(document).ready(function() {
        var discipliny = {{discipliny|safe}}; //создадим объект массива дисциплин группы
        var discnagryz = {{discnagryz|safe}}; //создадим объект массива нагрузки дисциплин

        var table = []; // Обьединённая таблица
        for (x in discipliny)
        {
            let item_table_nagryz = {}; // Часть строки таблицы
            for (i in discnagryz)
            {
                if (discnagryz[i].fields.id_disc == discipliny[x].pk)
                {
                    var item = discnagryz[i];
                    item_table_nagryz[item.fields.semestr] = item;
                }
            };
            var item_table_disc = discipliny[x];
            item_table_disc.nagryzka = item_table_nagryz;

            table.push(item_table_disc);
        }
        // $("#hhh").html(returnObj[1].fields.forma_obucheniya); // доступ к полям объекта
        for (item in table) {
            let new_el = document.createElement("tr");
            let text_1 = '<td t="disc" r="'+table[item].pk+'" c="disc_index">'+table[item].fields.disc_index+'</td>'+
                         '<td t="disc" r="'+table[item].pk+'" c="disciplina">'+table[item].fields.disciplina+'</td>'
            for (var c=1; c<={{group.max_sem}}; c++) {
            if (c == {{group.tek_sem}}) {style='style="background-color: var(--background-header-text); color: var(--background-header);"'} else {style=''}
            if (table[item].nagryzka[c] != null) {text_1 += '<td '+style+' t="nagr" r="'+table[item].nagryzka[c].pk'+" c="forma_attestacii-'+c+'"><a href="/vedomosty/'+table[item].nagryzka[c].pk+'/">'+table[item].nagryzka[c].fields.forma_attestacii+'</a></td>'}
                else {text_1 += `<td ${style} t="nagr" r="" c="forma_attestacii-${c}"></td>`}
            }
            let text_2 = '<td t="disc" r="'+table[item].pk+'" c="max_nagruzka">'+table[item].fields.max_nagruzka+'</td>'+
                            '<td t="disc" r="'+table[item].pk+'" c="samostoyatelnaya_raboa">'+table[item].fields.samostoyatelnaya_raboa+'</td>' +
                            '<td t="disc" r="'+table[item].pk+'" c="vsego_zanyatii">'+table[item].fields.vsego_zanyatii+'</td>' +
                            '<td t="disc" r="'+table[item].pk+'" c="lekcii">'+table[item].fields.lekcii+'</td>' +
                            '<td t="disc" r="'+table[item].pk+'" c="praktic">'+table[item].fields.praktic+'</td>' +
                            '<td t="disc" r="'+table[item].pk+'" c="kurs_podgotovka">'+table[item].fields.kurs_podgotovka+'</td>'
            let text_3 = "";
            for (var c=1; c<={{group.max_sem}}; c++) {
            if (c == {{group.tek_sem}}) {style='style="background-color: var(--background-header-text); color: var(--background-header);"'} else {style=''}
            if (table[item].nagryzka[c] != null) {text_3 += '<td '+style+' t="nagr" r="'+table[item].nagryzka[c].pk+'" c="chasov-'+c+'">'+table[item].nagryzka[c].fields.chasov+'</td>'}
                else {text_3 += '<td '+style+' t="nagr" r="" c="chasov-'+c+'"></td>`}
            }
            text = text_1+text_2+text_3;
            $("#insert").append(new_el);
            $(new_el).html(text);
        }

{% if user.is_authenticated %}
        $('#insert td').dblclick(function(e)	{
            //ловим элемент, по которому кликнули
            var t = e.target || e.srcElement;
            //ловим элемент, куда передать значение
            var target = t.parentElement;
            $(target).attr('target', 'target');
            $('#id').val($(target.cells[0]).attr('r'));
            $('#id_group').val({{group.pk}});
            for (var c=1; c<={{group.max_sem}}; c++) {
                $('#id_nagruz-'+c).val($(target.cells[1+c]).attr('r'));
                $('#forma_attestacii-'+c).val($(target.cells[1+c]).html());
                $('#chasov-'+c).val($(target.cells[{{group.max_sem}}+7+c]).html());
            }
            $('#disc_index').val($("tr[target='target'] td[c='disc_index']").html());
            $('#disciplina').val($("tr[target='target'] td[c='disciplina']").html());
            $('#max_nagruzka').val($("tr[target='target'] td[c='max_nagruzka']").html());
            $('#samostoyatelnaya_raboa').val($("tr[target='target'] td[c='samostoyatelnaya_raboa']").html());
            $('#vsego_zanyatii').val($("tr[target='target'] td[c='vsego_zanyatii']").html());
            $('#lekcii').val($("tr[target='target'] td[c='lekcii']").html());
            $('#praktic').val($("tr[target='target'] td[c='praktic']").html());
            $('#kurs_podgotovka').val($("tr[target='target'] td[c='kurs_podgotovka']").html());
            $(target).removeAttr('target', 'target');
            $('#modal-message').prop('checked', true);
        });
{% endif %}
    });