define
([
    'jquery','jquery/superdesk', 'gizmo/superdesk', 
    'gizmo/superdesk/action',
    config.cjs('views/auth.js'),
    'dust/core','jquery/tmpl','jquery/rest', 'bootstrap',  
    'tmpl!layouts/dashboard',
    'tmpl!navbar'
], 
function($, superdesk, Gizmo, Action, AuthApp)
{
    var MenuView = Gizmo.View.extend
    ({
        events: { "[data-logged-in]": { 'click' : 'loginHandler' } },
        
        /*!
         * gets menu and renders
         */
        refresh: function()
        {
            this.getMenu(this.render);
        },
        
        getMenu: function(cb)
        {
            var dfd = new $.Deferred,
                self = this;
                dfd.done(cb); 
        
            this.displayMenu = [];
            this.submenus = {};
                
            // TODO should not be here
            $.superdesk.applyLayout('layouts/dashboard', {}, function(){ Action.initApps('modules.dashboard.*', $($.superdesk.layoutPlaceholder)); });
            
            Action.getMore('menu.*').done(function(mainMenus)
            {
                self.displayMenu = [];
                Action.getMore('menu.*.*').done(function(subMenus)
                {
                    $(mainMenus).each(function()
                    {
                        hasSubs = false;
                        for( var i=0; i<subMenus.length; i++ )
                            if( subMenus[i].get('Path').indexOf(this.get('Path')) === 0 ) hasSubs = true;
                        if( hasSubs )
                        {
                            var Subs = 'data-submenu='+this.get('Path'),
                                Subz = '[data-submenu="'+this.get('Path')+'"]';
                            self.submenus[this.get('Path')] = this.get('Path') + '.*';
                        }
                        
                        self.displayMenu.push($.extend({}, this.feed(), 
                        { 
                            Path: this.get('Path').split('.'), 
                            Name: this.get('Path').replace('.', '-'),
                            Subs: Subs
                        }));
                    });
                    dfd.resolve(self);
                });
            }).
            // we still resolve it so we can display something
            fail(function(){ dfd.resolve(self); });
            
            return this;
        },
        init: function()
        {
            var self = this;
            this.displayMenu = [];
            
            $(AuthApp).on('login', function(){ $(this._dialog).dialog('close'); });
            $(AuthApp).on('login logout', function(){ self.refresh(); });
            
            this.el.on('refresh-menu', function(){ self.getMenu(self.render, 'refresh'); });
        },
        /*!
         * Deferred callback
         */
        render: function(view)
        {
            // make data for menu template
            var self = view,
                navData = {superdesk: {menu: self.displayMenu}};
            superdesk.login && $.extend(navData, {user: superdesk.login});

            self.el
            .html('')
            .tmpl('navbar', navData, function()
            {
                /*!
                 * for submenus, we get their corresponding build scripts
                 */
                self.el.find('[data-submenu]').each(function()
                {
                    var submenuElement = this;
                    Action.initApps(self.submenus[$(this).attr('data-submenu')], submenuElement, self.el);
                    
                    return true;
                    
                    Action.getMore( self.submenus[$(this).attr('data-submenu')] )
                    .done(function(subs)
                    {
                        $(subs).each(function()
                        { 
                            require([this.get('Script').href], function(submenuApp)
                            { 
                                submenuApp && submenuApp.init && submenuApp.init(submenuElement, self.el); 
                            }); 
                        });
                    });
                });
            })
            .off('click.superdesk')
            .on('click.superdesk', '.nav > li > a', function(event)
            {
                var self = this;
                if(!$(self).attr('href')) return;
                if(!$(self).attr('script-path')) { event.preventDefault(); return; }

                $(self).attr('data-loader') != 'false' && superdesk.showLoader();
                
                var callback = function()
                { 
                    require([$(self).attr('script-path')], function(x){ x && x.init && x.init(); });
                };
                  
                var href = $(self).attr('href').replace(/^\/+|\/+$/g, '');
                if( $.trim(href) != '' )
                    superdesk.navigation.bind( href, callback, $(self).text() || null );
                else
                    callback();
                
                event.preventDefault(); 
            });
            
            /*!
             * redirect to current page on reload
             */
            if( superdesk.navigation.getStartPathname() != '')
                self.el.find('li > a[href]').each(function()
                {
                    if( $(this).attr('href').replace(/^\/+|\/+$/g, '') == superdesk.navigation.getStartPathname()) 
                        $(this).trigger('click'); 
                });
            
            $('#navbar-logout', self.el) // TODO param.
            .off('click.superdesk')
            .on('click.superdesk', function()
            {
                AuthApp.logout();
                self.refresh();
            });
        },
        /*!
         * login control
         */
        loginHandler: function(evt)
        {
            if( $(evt.currentTarget).attr('data-logged-in') == 'false' ) AuthApp.renderPopup();
        }
        
    });
    
    return MenuView;
});