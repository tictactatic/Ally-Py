define
([
    'jquery', 'jquery/superdesk', 'gizmo/superdesk', 'utils/sha512',
    config.cjs('models/AuthToken.js'),
    config.cjs('models/AuthLogin.js'),
    'jquery/tmpl', 'jquery/rest', 'bootstrap',
    'tmpl!auth', 'tmpl!auth-page' 
],
function($, superdesk, gizmo, jsSHA, AuthToken, AuthLogin)
{
    var 
    /*!
     * performs login
     */
    AuthLoginApp = function(username, password, loginToken)
    {
        var 
            shaUser = new jsSHA(username, "ASCII"),
            shaPassword = new jsSHA(password, "ASCII"),         
            shaStep1 = new jsSHA(shaPassword.getHash("SHA-512", "HEX"), "ASCII"),
            shaStep2 = new jsSHA(loginToken, "ASCII"),          
            authLogin = new $.rest('Security/Authentication/Login').xfilter('User.Name,User.Id,User.EMail');
            
            HashedToken = shaStep1.getHMAC(username, "ASCII", "SHA-512", "HEX");            
            HashedToken = shaStep2.getHMAC(HashedToken, "ASCII", "SHA-512", "HEX");
            authLogin.resetData().insert
            ({
                UserName: username,
                Token: loginToken, 
                HashedToken: HashedToken
            })
            .done(function(data)
            {
                var user = data.User;
                
                // h4xx to set login href.. used in menu to get actions path
                localStorage.setItem('superdesk.login.selfHref', (data.User.href.indexOf('my/') === -1 ? data.User.href.replace('resources/','resources/my/') : data.User.href) );
                // /h4axx
                
                localStorage.setItem('superdesk.login.session', data.Session);
                localStorage.setItem('superdesk.login.id', user.Id);
                localStorage.setItem('superdesk.login.name', user.Name);
                localStorage.setItem('superdesk.login.email', user.EMail);
                $.restAuth.prototype.requestOptions.headers.Authorization = localStorage.getItem('superdesk.login.session');
                superdesk.login = {Id: localStorage.getItem('superdesk.login.id'), Name: localStorage.getItem('superdesk.login.name'), EMail: localStorage.getItem('superdesk.login.email')}
                $(authLogin).trigger('success');
        });
        return $(authLogin);
    },
    AuthTokenApp = function(username, password) 
    {
        // new token model
        var authToken = new AuthToken;
        authToken.set({ userName: username }).sync()
        .done(function(data)
        {
            // attempt login after we got token
            authLogin = new AuthLogin;
            authLogin.authenticate(username, password, data.Token)
            .done(function(data)
            {
                var user = data.User;
                
                    // h4xx to set login href.. used in menu to get actions path
                localStorage.setItem('superdesk.login.selfHref', (data.User.href.indexOf('my/') === -1 ? data.User.href.replace('resources/','resources/my/') : data.User.href) );
                // /h4axx
                
                localStorage.setItem('superdesk.login.session', data.Session);
                localStorage.setItem('superdesk.login.id', user.Id);
                localStorage.setItem('superdesk.login.name', user.Name);
                localStorage.setItem('superdesk.login.email', user.EMail);
                $.restAuth.prototype.requestOptions.headers.Authorization = localStorage.getItem('superdesk.login.session');
                superdesk.login = {Id: localStorage.getItem('superdesk.login.id'), Name: localStorage.getItem('superdesk.login.name'), EMail: localStorage.getItem('superdesk.login.email')}
                $(authLogin).trigger('success');
            });
            authLogin.on('failed', function()
            {
                $(authToken).trigger('failed', 'authToken');
            })
            .on('success', function()
            {
                $(authToken).trigger('success');
            });
        });
        return authToken;
    },
    
    AuthApp = gizmo.View.extend( 
    {
        success: $.noop,
        showed: false,
        require: function()
        {
            if(AuthApp.showed) return;
            var self = this,
                data = this.loginExpired ? {'expired': true} : {}; // rest
            AuthApp.showed = true;  
            $.tmpl('auth', data, function(e, o)
            { 
                var dialog = $(o).eq(0).dialog
                    ({ 
                        draggable: false,
                        resizable: false,
                        modal: true,
                        width: "40.1709%",
                        buttons: 
                        [
                             { text: "Login", click: function(){ $(form).trigger('submit'); }, class: "btn btn-primary"},
                             { text: "Close", click: function(){ $(this).dialog('close'); }, class: "btn"}
                        ],
                        close: function(){ $(this).remove(); AuthApp.showed = false; }
                    }),
                    form = dialog.find('form');
                
                form.off('submit.superdesk')
                .on('submit.superdesk', function(event)
                {
                    var username = $(this).find('#username'), 
                        password = $(this).find('#password'),
                        alertmsg = $(this).find('.alert');
                    
                    AuthTokenApp(username.val(), password.val())
                        .on('failed', function(evt, type)
                        { 
                            password.val('');
                            username.focus();
                            alertmsg.removeClass('hide');
                        })
                        .on('success', function(evt)
                        { 
                            AuthApp.success && AuthApp.success(); 
                            $(dialog).dialog('close'); 
                            AuthApp.showed = false; 
                            $(AuthApp).trigger('authenticated');
                        });
                    event.preventDefault();
                    
                });
                
            });
        },
        events:
        {
            'form': { 'submit': 'login' }
        },
        login: function(event)
        {
            var username = $(this.el).find('#username'), 
                password = $(this.el).find('#password'),
                alertmsg = $(this.el).find('.alert'),
                self = this;
        
            // make new authentication process
            AuthTokenApp(username.val(), password.val()) 
            .on('failed', function(evt, type)
            { 
                password.val('');
                username.focus();
                alertmsg.removeClass('hide');
                $(self).triggerHandler('login-failed');
            })
            .on('success', function(evt)
            { 
                $(self).triggerHandler('login');
            });
            event.preventDefault();
        },
        render: function()
        {
            var self = this;
            $.tmpl('auth-page', {}, function(e, o){ self.el.html(o); });
        }
    });
    
    return new AuthApp;
});