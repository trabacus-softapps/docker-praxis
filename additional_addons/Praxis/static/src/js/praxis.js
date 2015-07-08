openerp.Praxis = function(openerp) {
	var instance = openerp;
var _t = instance.web._t,
   _lt = instance.web._lt;
var QWeb = instance.web.qweb;

/*

openerp.web.form.widgets.add('timepicker','openerp.web.form.timepicker');
openerp.web.form.timepicker = openerp.web.form.FieldDatetime.extend(
    {    
       template: 'timepicker',
       type_of_date: "datetime",
       
       build_widget: function() {
        return new instance.web.DateTimeWidget(this);
    },
       
       events: {
        'dp.change .oe_datepicker_main': 'change_datetime',
        'dp.show .oe_datepicker_main': 'set_datetime_default',
        'change .oe_datepicker_master': 'change_datetime',
    },
      

      
      

        init: function (view, code) {
            this._super(view, code);
            console.log('loading...');
            if (!this.get("effective_readonly")) {
        	console.log('ERROR');
            this.datewidget = this.build_widget();
            this.datewidget.on('datetime_changed', this, _.bind(function() {
                this.internal_set_value(this.datewidget.get_value());
            }, this));
            this.datewidget.appendTo(this.$el);
            this.setupFocus(this.datewidget.$input);
        }
        },

       
       
       initialize_content: function() {
        if (!this.get("effective_readonly")) {
        	console.log('ERROR');
            this.datewidget = this.build_widget();
            this.datewidget.on('datetime_changed', this, _.bind(function() {
                this.internal_set_value(this.datewidget.get_value());
            }, this));
            this.datewidget.appendTo(this.$el);
            this.setupFocus(this.datewidget.$input);
        }
    },
    
    focus: function() {
        var input = this.datewidget && this.datewidget.$input[0];
        return input ? input.focus() : false;
    },
    
    destroy_content: function() {
        if (this.datewidget) {
            this.datewidget.destroy();
            this.datewidget = undefined;
        }
    },
    
    render_value: function() {
    	console.log('inside render');
        if (!this.get("effective_readonly")) {
            this.datewidget.set_value(this.get('value'));
        } else {
            this.$el.text(instance.web.format_value(this.get('value'), this, ''));
        }
    },
      
       
       start: function() {
    	
        var self = this;
        var l10n = _t.database.parameters;
        
        var self = this;
        var l10n = _t.database.parameters;
        var options = {
            pickTime: true,
            //pickDate : false,
            useSeconds: true,
            startDate: moment({ y: 1900 }),
            endDate: moment().add(200, "y"),
            calendarWeeks: true,
            icons : {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down'
               },
            language : moment.locale(),
            format : instance.web.normalize_format(l10n.date_format +' '+ l10n.time_format),
        };
        this.$input = this.$el.find('input.oe_datepicker_master');
        if (this.type_of_date === 'date') {
            options['pickTime'] = false;
            options['pickDate'] = false;
            options['useSeconds'] = false;
            options['format'] = instance.web.normalize_format(l10n.date_format);
        }
        
         if (this.type_of_date === 'datetime') {
            options['pickDate'] = false;
        }
        
       
       
              
        this.picker = this.$('.oe_datepicker_main').datetimepicker({
                    format: instance.web.normalize_format(l10n.time_format)
                });
        
        console.log('this.$input',this.$input);
               
        this.picker = this.$('.oe_datepicker_main').datetimepicker(options);
       this.set_readonly(false);
       this.set({'value': false});
    },
    
    // set_value: function(value_) {
        // this.set({'value': value_});
        // this.$input.val(value_ ? this.format_client(value_) : '');
    // },
    get_value: function() {
    	console.log("get");
        return this.get('value');
    },
    set_value_from_ui_: function() {
    	var l10n = _t.database.parameters;
        var value_ = this.$input.val() || false;
        var date = new Date();
        date_format = instance.web.normalize_format(l10n.date_format);
        time_format = instance.web.normalize_format(l10n.date_format +' '+ l10n.time_format);
        console.log('format', instance.web.normalize_format(l10n.date_format));
        dateformat = (date.getMonth() + 1) + '/' + date.getDate() + '/' +  date.getFullYear();
        //alert((date.getMonth() + 1) + '/' + date.getDate() + '/' +  date.getFullYear());
        if (value_){
	        var datetime = new Date( dateformat +' '+ value_);
	        dates = moment(datetime, "YYYY-MM-DD HH:mm");
	        value_ = moment(datetime).format(time_format);
	       }
        console.log("Value_", moment(datetime).format(time_format));
        
        this.set_value(this.parse_client(value_));
    },
    
    set_readonly: function(readonly) {
        this.readonly = readonly;
        this.$input.prop('readonly', this.readonly);
    },
    
    is_valid_: function() {
        var value_ = this.$input.val();
        if (value_ === "") {
            return true;
        } else {
            try {
                this.parse_client(value_);
                return true;
            } catch(e) {
                return false;
            }
        }
    },
    parse_client: function(v) {
        return instance.web.parse_value(v, {"widget": this.type_of_date});
    },
    format_client: function(v) {
        return instance.web.format_value(v, {"widget": this.type_of_date});
    },
    set_datetime_default: function(){
        //when opening datetimepicker the date and time by default should be the one from
        //the input field if any or the current day otherwise
        if (this.type_of_date === 'datetime') {
            value = moment().second(0);
            if (this.$input.val().length !== 0 && this.is_valid_()){
                var value = this.$input.val();
            }
            this.$('.oe_datepicker_main').data('DateTimePicker').setValue(value);
        }
    },
    change_datetime: function(e) {
    	console.log("value......",e);
    	 this.set_value_from_ui_();
         this.trigger("datetime_changed");
        // if ((e.type !== "keypress" || e.which === 13) && this.is_valid_()) {
            // this.set_value_from_ui_();
            // this.trigger("datetime_changed");
        // }
    },
    commit_value: function () {
        this.change_datetime();
    },
    
    
       
});

*/

/*        New Functionality */


/*
instance.web.TimeWidget = instance.web.DateTimeWidget.extend({
    type_of_date: "time"
    
});

instance.web.form.widgets.add('FieldTime','openerp.web.form.FieldTime');
instance.web.form.FieldTime = instance.web.form.FieldDatetime.extend({
    template: "FieldTime",
    build_widget: function() {
    	console.log('inside picker');
        return new instance.web.TimeWidget(this);
    },
    
    init: function (view, code) {
    	this._super(view, code);
    	console.log('inside picker');
    },
    
    
});
*/

openerp.web.form.widgets.add('custom_time', 'openerp.Praxis.custom_time');
  openerp.Praxis.custom_time = openerp.web.form.FieldChar.extend({
    template:'custom_time',
    type_of_date: "time",
    
    events: {
        'dp.change .oe_datepicker_main': 'change_time',
        'change .oe_datepicker_master': 'change_time',
      },
       
    
       init: function (field_manager, node) {
            this._super(field_manager, node);
            console.log('loading...');
        },
       
        initialize_content: function() {
       	this._super();
        this.setupFocus(this.$('input'));
    },
       
       start:function(){
       	var l10n = _t.database.parameters;
        this._super.apply(this, arguments);
        var self = this;
        var options = {
            pickTime: true,
            useSeconds: true,
            startDate: moment({ y: 1900 }),
            endDate: moment().add(200, "y"),
            calendarWeeks: true,
            icons : {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down'
               },
            language : moment.locale(),
            pickTime: true,
            pickDate : false,
            useSeconds : false,
            format : instance.web.normalize_format(l10n.time_format),
        };
        
        //this.$('.datepickerbutton1').datetimepicker(options);
        $('.oe_datepicker_main').datetimepicker(options);
        
        	
       },
       
       change_time: function(e) {
       	var self = this;
       	console.log('inside change datetimr', e.which);
       	this.set_value_from_ui_time();
       	this.trigger("datetime_changed");
        //if((e.type !== "keypress" || e.which === 13) && this.is_syntax_valid()) {
         //   this.set_value_from_ui_time();
         //   this.trigger("datetime_changed");
            
            
        //}
    },
    
    
    set_value_from_ui_time: function() {
    	var self = this;
    	console.log("inside1",self.$el.find('input').val());
        var value_ = this.$('input').val() || false;
        this.set_value_time(value_);
    },
    
    set_value_time: function(value_) {
    	var self = this;
    	this.set({'value': value_});
        this.$('input').val(value_ ? value_ : '');
    },
    


    
     /*initialize_content: function() {
    	var l10n = _t.database.parameters;
        this._super();
        var self = this;
        
        
        
       $('input').on('keyup', function(event) {
     		self.$el.find('input').val(self.$el.find('input').val().toUpperCase());
        });
        
    },*/
  
  });




};
