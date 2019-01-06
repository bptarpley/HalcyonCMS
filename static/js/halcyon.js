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

var custom_editor;

if (default_header_css == null) {
    var default_header_css = "row no-gutters dark-gray mt-15";
}

if (default_row_css == null) {
    var default_row_css = "row no-gutters";
}

if (default_col_css == null) {
    var default_col_css = "content-block white";
}

// ********************************************
// SECTION EDITING FUNCTIONS
// ********************************************

function new_section(order) {
    $('#sec-layout-json').val('{}');
    $('#sec-layout-box').html('');
    $('#sec-col-settings-div').html('');

    $('#sec-id').val('new');
    $('#sec-order').val(order);
    $('#sec-name').val('');
    $('#sec-header-text').val('');
    $('#sec-header-css').val(default_header_css);
    $('#sec-show-header').prop('checked', true);
    $('#section-modal').modal();
}

function edit_section(section_id) {
    $.get('/get-section/', {'section-id': section_id}, function(data){
        if ('id' in data) {
            $('#sec-layout-box').html('');
            for (let x = 0; x < data.rows.length; x++) {
                add_row(
                    data.rows[x].id,
                    false,
                    data.rows[x].css,
                    data.rows[x].order
                );

                for (let y = 0; y < data.rows[x].cols.length; y++) {
                    add_column(
                        data.rows[x].id,
                        data.rows[x].cols[y].id,
                        data.rows[x].cols[y].width,
                        data.rows[x].cols[y].is_custom,
                        data.rows[x].cols[y].css,
                        data.rows[x].cols[y].order
                    );
                }
            }

            $('#sec-id').val(data.id);
            $('#sec-order').val(data.order);
            $('#sec-header-text').val(data.header_text);
            $('#sec-header-css').val(data.header_css);
            $('#sec-header-name').val(data.name);
            $('#sec-show-header').prop('checked', data.show_header);
            $('#sec-full-width').prop('checked', data.full_width);
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

function add_row(row_id=-1, add_first_column=true, css=default_row_css, order=-1) {
    // Get New Row ID if none passed in
    if (row_id < 0) {
        row_id = 'new' + $('#sec-num-rows').val();
    }
    let num_rows = parseInt($('#sec-num-rows').val()) + 1;

    if (order < 0) {
        order = 0;
        $(`#sec-layout-row-${row_id} .row-order-input`).each(function () {
            if (parseInt($(this).val()) > order) {
                order = parseInt($(this).val());
            }
        });
        order += 1;
    }

    // Setup Row Header
    let new_row_header = `
        <div id="sec-layout-row-${row_id}-header" class="row">
            <div class="col-sm-12 sec-layout-row-header">
                <input type="hidden" id="sec-layout-row-${row_id}-num-cols" value="0" />
                <input type="hidden" id="sec-layout-row-${row_id}-total-width" value="0" />
                <input type="hidden" id="sec-layout-row-${row_id}-order" class="row-order-input" value="${order}" />
                
                <a href="javascript: add_column('${row_id}');">
                    Add Column
                </a> | 
                <a href="javascript: delete_row('${row_id}');">
                    Delete Row
                </a> |
                CSS: <input type="text" id="sec-layout-row-${row_id}-css" value="${css}" />
            </div>
        </div>
    `;
    $('#sec-layout-box').append(new_row_header);

    // Setup Row
    $('#sec-layout-box').append(`<div id="sec-layout-row-${row_id}" class="row sec-layout-row"></div>`);

    // Add first column
    if (add_first_column) {
        add_column(row_id);
    }

    $('#sec-num-rows').val(num_rows);
}

function add_column(row_id, col_id=-1, col_width=-1, is_custom=false, css=default_col_css, order=-1) {
    var row_width = parseInt($(`#sec-layout-row-${row_id}-total-width`).val());
    if (row_width >= 12) {
        show_layout_alert("<strong>There is not enough room to add another column</strong>. Resize or delete existing columns.");
    }
    else {
        if (col_id < 0) {
            col_id = 'new' + $(`#sec-layout-row-${row_id}-num-cols`).val();
        }

        if (col_width < 0) {
            col_width = 12 - row_width;
        }

        if (order < 0) {
            order = 0;
            $(`#sec-layout-row-${row_id} .col-order-input`).each(function () {
                if (parseInt($(this).val()) > order) {
                    order = parseInt($(this).val());
                }
            });
            order += 1;
        }

        $(`#sec-layout-row-${row_id}`).append(section_col_template(row_id, col_id, col_width, is_custom, css, order));
        $(`#sec-layout-row-${row_id}-num-cols`).val(parseInt($(`#sec-layout-row-${row_id}-num-cols`).val()) + 1);
        $(`#sec-layout-row-${row_id}-total-width`).val(parseInt(row_width) + parseInt(col_width));
    }
}

function delete_row(row_id) {
    $(`#sec-layout-row-${row_id}-header`).remove();
    $(`#sec-layout-row-${row_id}`).remove();
}

function section_col_template(row_id, col_id, col_size, is_custom, css, order) {
    var custom = 0;
    if (is_custom) {
        custom = 1;
    }

    return `<div id="sec-layout-row-${row_id}-col-${col_id}" class="col-sm-${col_size} sec-layout-col" onclick="select_col('${row_id}', '${col_id}');">
        <input type="hidden" id="sec-layout-row-${row_id}-col-${col_id}-size" value="${col_size}" />
        <input type="hidden" id="sec-layout-row-${row_id}-col-${col_id}-custom" value="${custom}" />
        <input type="hidden" id="sec-layout-row-${row_id}-col-${col_id}-css" value="${css}" />
        <input type="hidden" id="sec-layout-row-${row_id}-col-${col_id}-order" class="col-order-input" value="${order}" />   &nbsp;
    </div>`;
}

function select_col(row_id, col_id) {
    $('.sec-layout-col').removeClass('sec-layout-col-selected');
    $(`#sec-layout-row-${row_id}-col-${col_id}`).addClass('sec-layout-col-selected');

    $('#sec-col-settings-div').html(`
        <div class="form-group">
            <label for="sec-layout-row-${row_id}-col-${col_id}-sizer">Width</label>
            <select class="form-control" id="sec-layout-row-${row_id}-col-${col_id}-sizer" onchange="change_column_size('${row_id}', '${col_id}');">
                <option value="1">1</option><option value="2">2</option><option value="3">3</option>
                <option value="4">4</option><option value="5">5</option><option value="6">6</option>
                <option value="7">7</option><option value="8">8</option><option value="9">9</option>
                <option value="10">10</option><option value="11">11</option><option value="12">12</option>
            </select>
        </div>
        <div class="form-check-inline">
            <input class="form-check-input" type="checkbox" id="sec-layout-row-${row_id}-col-${col_id}-custom-box" onchange="change_column_custom('${row_id}', '${col_id}');"/>
            <label for="sec-layout-row-${row_id}-col-${col_id}-custom-box">Custom HTML?</label>
        </div>
        <div class="form-group">
            <label for="sec-layout-row-${row_id}-col-${col_id}-css-box">CSS</label>
            <input type="text" class="form-control" id="sec-layout-row-${row_id}-col-${col_id}-css-box" onchange="change_column_css('${row_id}', '${col_id}');" />
        </div>
        <div class="form-group">
            <button type="button" class="btn btn-danger" onclick="delete_column('${row_id}', '${col_id}');">Delete Column</button>
        </div>
    `);

    $(`#sec-layout-row-${row_id}-col-${col_id}-sizer`).val($(`#sec-layout-row-${row_id}-col-${col_id}-size`).val());
    $(`#sec-layout-row-${row_id}-col-${col_id}-custom-box`).prop('checked', $(`#sec-layout-row-${row_id}-col-${col_id}-custom`).val() == "1");
    $(`#sec-layout-row-${row_id}-col-${col_id}-css-box`).val($(`#sec-layout-row-${row_id}-col-${col_id}-css`).val());
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

function change_column_custom(row_id, col_id) {
    let checked = 0;
    if ($(`#sec-layout-row-${row_id}-col-${col_id}-custom-box`).is(':checked')) {checked = 1;}
    $(`#sec-layout-row-${row_id}-col-${col_id}-custom`).val(checked);
}

function change_column_css(row_id, col_id) {
    $(`#sec-layout-row-${row_id}-col-${col_id}-css`).val($(`#sec-layout-row-${row_id}-col-${col_id}-css-box`).val());
}

function delete_column(row_id, col_id) {
    // Remove the column
    let col = $(`#sec-layout-row-${row_id}-col-${col_id}`);
    col.remove();

    // Calculate new col count and row width
    let num_cols = 0;
    let row_width = 0;

    $(`#sec-layout-row-${row_id} > .sec-layout-col`).each(function () {
        num_cols += 1;
        let current_col_id = $(this).attr('id').replace(`sec-layout-row-${row_id}-col-`, '');
        row_width += parseInt($(`#sec-layout-row-${row_id}-col-${current_col_id}-size`).val());
    });

    $(`#sec-layout-row-${row_id}-total-width`).val(row_width);
    $('#sec-col-settings-div').html('');
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
        'rows': []
    };

    $('#sec-layout-box > .sec-layout-row').each(function () {
        var row_id = this.id.replace("sec-layout-row-", "");
        var row_index = layout_json['rows'].push({
            'id': row_id,
            'css': $(`#sec-layout-row-${row_id}-css`).val(),
            'order': parseInt($(`#sec-layout-row-${row_id}-order`).val()),
            'cols': []
        }) - 1;

        $(`#sec-layout-row-${row_id} > .sec-layout-col`).each(function () {
            var col_id = this.id.replace(`sec-layout-row-${row_id}-col-`, "");
            var col_prefix = '#' + this.id + '-';

            layout_json['rows'][row_index]['cols'].push({
                'id': col_id,
                'size': parseInt($(col_prefix + 'size').val()),
                'is_custom': $(col_prefix + 'custom').val() == "1",
                'css': $(col_prefix + 'css').val(),
                'order': parseInt($(col_prefix + 'order').val()),
            });
        });
    });

    return layout_json;
}

// ********************************************
// CUSTOM CONTENT EDITING FUNCTIONS
// ********************************************

function show_custom_editor(col_id) {
    var editor_div = $('#custom-editor-div');
    editor_div.html(`
        <div id='custom-editor'></div>
        <input type="hidden" name="column-id" value="${col_id}">
        <input type="hidden" id="custom-edit-new-content" name="new-content" value="">
        <input type="hidden" name="custom-content-save" value="y">
    `);

    var content = $.trim($(`#section-content-${col_id}`).html());
    custom_editor = ace.edit("custom-editor");
    custom_editor.setTheme("ace/theme/monokai");
    custom_editor.getSession().setMode("ace/mode/html");
    custom_editor.setValue(content);
    $('#content-edit-modal').modal();
}

function save_custom_edit() {
    var content = $.trim(custom_editor.getValue());
    $('#custom-edit-new-content').val(content);
    $('#content-edit-form').submit();
}
