// ********************************************
// MAIN SITE UTILITIES
// ********************************************

function scroll_to_section(section_name) {
    var section_tag = $("a[name='"+ section_name +"']");
    if ($(window).width() > medium_pixel_width) {
        $('html,body').animate({scrollTop: section_tag.offset().top - 55}, 'slow');
    } else {
        $('html,body').animate({scrollTop: section_tag.offset().top - 50}, 'slow');
    }
}

function logout() {

}

// ********************************************
// SECTION EDITING FUNCTIONS
// ********************************************

function new_section() {
    $('#sec-layout-json').val('{}');
    $('#sec-layout-box').html('');

    $('#sec-id').val('new');
    $('#sec-name').val('');
    $('#sec-header-text').val('');
    $('#sec-header-css').val('');
    $('#sec-show-header').prop('checked', true);
    $('#section-modal').modal();
}

function edit_section(section_id) {
    $.get('/get-section/', {'section-id': section_id}, function(data) {
        if ('section' in data) {
            $('#sec-layout-box').html('');
            for (var row_id in data['section']['layout']['rows']) {
                add_row(row_id, false);
                for (var col_id in data['section']['layout']['rows'][row_id]['cols']) {
                    add_column(
                        row_id,
                        col_id,
                        data['section']['layout']['rows'][row_id]['cols'][col_id]['width'],
                        data['section']['layout']['rows'][row_id]['cols'][col_id]['is_custom']
                    );
                    if ('content_id' in data['section']['layout']['rows'][row_id]['cols'][col_id]) {
                        var content_id_input = `<input type="hidden"
                                id="sec-layout-row-${row_id}-col-${col_id}-content-id"
                                value="${data['section']['layout']['rows'][row_id]['cols'][col_id]['content_id']}" />`;
                        $(`#sec-layout-row-${row_id}-col-${col_id}`).append(content_id_input);
                    }
                }
            }

            $('#sec-layout-json').val(JSON.stringify(data['section']['layout']));
            $('#sec-id').val(section_id);
            $('#sec-header-text').val(data['section']['header_text']);
            $('#sec-header-css').val(data['section']['header_css']);
            $('#sec-header-name').val(data['section']['name']);
            $('#section-modal').modal();
        }
    });
}

function save_section() {
    $('#sec-layout-json').val(JSON.stringify(get_layout_json()));
    $('#sec-layout-form').submit();
}

function delete_section() {
    $("<input type='hidden' name='delete-section' value='y' />").appendTo($('#sec-layout-form'));
    save_section();
}

function section_row_header_template(row_id) {
    return `<div class="col-sm-12 sec-layout-row-header">
        <input type="hidden" id="sec-layout-row-${row_id}-num-cols" value="0" />
        <input type="hidden" id="sec-layout-row-${row_id}-total-width" value="0" />
        <a href="javascript: add_column(${row_id});">
            Add Column
        </a> | 
        <a href="javascript: delete_row(${row_id});">
            Delete Row
        </a></div>`;
}

function section_col_template(row_id, col_id, col_size, is_custom=false) {
    var custom = "";
    if (is_custom) {
        custom = "checked";
    }

    return `<div id="sec-layout-row-${row_id}-col-${col_id}" class="col-sm-${col_size} sec-layout-col">
        <input type="hidden" id="sec-layout-row-${row_id}-col-${col_id}-size" value="${col_size}" />
        Width
        <select id="sec-layout-row-${row_id}-col-${col_id}-sizer" onchange="change_column_size(${row_id}, ${col_id});">
            <option value="1">1</option><option value="2">2</option><option value="3">3</option>
            <option value="4">4</option><option value="5">5</option><option value="6">6</option>
            <option value="7">7</option><option value="8">8</option><option value="9">9</option>
            <option value="10">10</option><option value="11">11</option><option value="12" selected>12</option>
        </select><br>
        <span class="oi oi-document"></span><input type="checkbox" id="sec-layout-row-${row_id}-col-${col_id}-custom" ${custom}/><br>
        <a href="javascript: delete_column(${row_id}, ${col_id});"<span class="oi oi-trash"></span>
    </div>`;
}

function add_row(row_id=-1, add_first_column=true) {
    // Get New Row ID if none passed in
    if (row_id < 0) {
        row_id = $('#sec-num-rows').val();
        var col_id = 0;
    }

    // Setup Row Header
    var new_row_header = $('<div/>');
    new_row_header.attr('id', "sec-layout-row-" + row_id + "-header");
    new_row_header.addClass('row');
    new_row_header.html(section_row_header_template(row_id));
    new_row_header.appendTo($('#sec-layout-box'));

    // Setup Row
    var new_row = $('<div/>');
    new_row.attr('id', `sec-layout-row-${row_id}`);
    new_row.addClass('row');
    new_row.addClass('sec-layout-row');
    new_row.appendTo($('#sec-layout-box'));

    // Add first column
    if (add_first_column) {
        add_column(row_id);
    }

    $('#sec-num-rows').val(parseInt(row_id) + 1);
}

function add_column(row_id, col_id=-1, col_width=-1, is_custom=false) {
    console.log(col_width);
    var row_width = parseInt($(`#sec-layout-row-${row_id}-total-width`).val());
    if (row_width >= 12) {
        show_layout_alert("<strong>There is not enough room to add another column</strong>. Resize or delete existing columns.");
    }
    else {
        if (col_id < 0) {
            col_id = $(`#sec-layout-row-${row_id}-num-cols`).val();
        }

        if (col_width < 0) {
            col_width = 12 - row_width;
        }

        $(`#sec-layout-row-${row_id}`).append(section_col_template(row_id, col_id, col_width, is_custom));

        $(`#sec-layout-row-${row_id}-col-${col_id}-sizer`).val(col_width);

        $(`#sec-layout-row-${row_id}-num-cols`).val(parseInt(col_id) + 1);
        $(`#sec-layout-row-${row_id}-total-width`).val(row_width + col_width);
    }
}

function change_column_size(row_id, col_id) {
    var row_size = parseInt($(`#sec-layout-row-${row_id}-total-width`).val());
    var old_size = parseInt($(`#sec-layout-row-${row_id}-col-${col_id}-size`).val());
    var new_size = parseInt($(`#sec-layout-row-${row_id}-col-${col_id}-sizer`).val());

    if (new_size < old_size) {
        var difference = old_size - new_size;
        row_size = row_size - difference;
    } else if (new_size > old_size) {
        var difference = new_size - old_size;
        row_size = row_size + difference;
    }

    if (row_size <= 12) {
        var col = $(`#sec-layout-row-${row_id}-col-${col_id}`);
        col.removeClass();
        col.addClass(`col-sm-${new_size}`);
        col.addClass('sec-layout-col');
        $(`#sec-layout-row-${row_id}-total-width`).val(row_size);
        $(`#sec-layout-row-${row_id}-col-${col_id}-size`).val(new_size);
    } else {
        show_layout_alert(`<strong>The selected column width was too big</strong>, as the total width of any row's columns cannot exceed 12.`);
        $(`#sec-layout-row-${row_id}-col-${col_id}-sizer`).val(old_size);
    }
}

function delete_column(row_id, col_id) {
    // Remove the column
    var col = $(`#sec-layout-row-${row_id}-col-${col_id}`);
    col.remove();

    // Calculate new col count and row width
    var num_cols = 0;
    var row_width = 0;

    $(`#sec-layout-row-${row_id} > .sec-layout-col`).each(function () {
        num_cols += 1;
        row_width += get_layout_column_width(row_id, col_id);
    });

    $(`#sec-layout-row-${row_id}-total-width`).val(row_width);
}

function delete_row(row_id) {
    $(`#sec-layout-row-${row_id}-header`).remove();
    $(`#sec-layout-row-${row_id}`).remove();
}

function get_layout_column_width(row_id, col_id) {
    return $(`#sec-layout-row-${row_id}-col-${col_id}-sizer`).val();
}

function get_layout_column_custom(row_id, col_id) {
    return $(`#sec-layout-row-${row_id}-col-${col_id}-custom`).is(':checked');
}

function show_layout_alert(msg) {
    $('#sec_layout_alert_box').append(`<div class="alert alert-warning alert-dismissible fade show" role="alert">
        ${msg}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
        </button>
    </div>`);
}

function get_layout_json() {
    var layout_json = {
        'rows': {}
    };

    $('#sec-layout-box > .sec-layout-row').each(function () {
        var row_id = this.id.replace("sec-layout-row-", "");
        layout_json['rows'][row_id] = {
            'cols': {}
        };

        $(`#sec-layout-row-${row_id} > .sec-layout-col`).each(function () {
            var col_id = this.id.replace(`sec-layout-row-${row_id}-col-`, "");
            var column = $('#' + this.id);

            layout_json['rows'][row_id]['cols'][col_id] = {
                'width': get_layout_column_width(row_id, col_id),
                'is_custom': get_layout_column_custom(row_id, col_id)
            };

            if($(`#sec-layout-row-${row_id}-col-${col_id}-content-id`).length) {
                layout_json['rows'][row_id]['cols'][col_id]['content_id'] = $(`#sec-layout-row-${row_id}-col-${col_id}-content-id`).val();
            }
        });
    });

    return layout_json;
}

// ********************************************
// CUSTOM CONTENT EDITING FUNCTIONS
// ********************************************

function show_custom_editor(content_id) {
    var editor_div = $('#custom-editor-div');
    editor_div.html(`
        <textarea id='custom_editor'></textarea>
        <input type="hidden" name="content-id" value="${content_id}">
        <input type="hidden" id="custom-edit-new-content" name="new-content" value="">
        <input type="hidden" name="custom-content-save" value="y">
    `);

    var content = $.trim($(`#section-content-${content_id}`).html());
    $('#custom_editor').val(content);
    CKEDITOR.replace('custom_editor', {
        startupMode: 'source'
    });
    $('#content-edit-modal').modal();
}

function save_custom_edit() {
    var content = $.trim(CKEDITOR.instances.custom_editor.getData());
    $('#custom-edit-new-content').val($.base64Encode(content));
    $('#content-edit-form').submit();
}
