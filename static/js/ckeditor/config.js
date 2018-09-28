/**
 * @license Copyright (c) 2003-2017, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */

// Uncomment out two lines below to use the visual toolbar configurator.
// var csrf_token = "";
// var page_id = 0;

CKEDITOR.editorConfig = function( config ) {
	// Define changes to default configuration here.
	// For complete reference see:
	// http://docs.ckeditor.com/#!/api/CKEDITOR.config

	// The toolbar groups arrangement, optimized for two toolbar rows.

	config.toolbarGroups = [
		{ name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
		{ name: 'undo', groups: [ 'undo' ] },
		{ name: 'links', groups: [ 'links' ] },
		{ name: 'insert', groups: [ 'insert' ] },
		{ name: 'forms', groups: [ 'forms' ] },
		{ name: 'tools', groups: [ 'tools' ] },
		{ name: 'others', groups: [ 'others' ] },
		{ name: 'paragraph', groups: [ 'list', 'indent', 'blocks', 'align', 'bidi', 'paragraph' ] },
		{ name: 'styles', groups: [ 'styles' ] },
		{ name: 'colors', groups: [ 'colors' ] },
		{ name: 'about', groups: [ 'about' ] }
	];

	config.removeButtons = 'Underline,Subscript,Superscript,Styles,Maximize,Source,About';

	// Set the most common block elements.
	config.format_tags = 'p;h1;h2;h3;pre';

	// Simplify the dialog windows.
	config.removeDialogTabs = 'image:advanced;link:advanced';

	// config.extraPlugins = 'inlinesave,stylesheetparser';
	config.extraPlugins = 'inlinesave';

	config.inlinesave = {
		postUrl: '',
		postData: {csrfmiddlewaretoken: csrf_token, page_id: page_id, content_save: 'y'},
		onSave: function(editor) { console.log('clicked save', editor); return true; },
		onSuccess: function(editor, data) { console.log('save successful', editor, data); },
		onFailure: function(editor, status, request) { console.log('save failed', editor, status, request); },
		successMessage: 'Content saved!',
		errorMessage: 'Error saving content.',
		useJSON: false,
		useColorIcon: false
	};

	config.stylesSet = [];
	config.filebrowserBrowseUrl = '/admin/filebrowser/browse?pop=3';
};
