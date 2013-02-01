define([ 'gizmo/superdesk', 'jquery', 'gizmo/superdesk/models/actions' ], 
function( gizmo, $, Actions )
{
    var cache = {},
        actions = new Actions;
    gizmo.Superdesk.action =
    {
        actions: actions,
        /*!
         * @param string path 
         * @returns $.Deferred()
         */
        getMore: function(path, url)
        {
            var dfd = new $.Deferred,

                searchCache = function()
                {
                    var results = [], searchPath = path; 
                    //if( path.lastIndexOf('*') === path.length-1 ) searchPath = path.substr(0, path.length-1);
                    searchPath = searchPath.split('*').join('%').replace(/([.?*+^$[\]\\(){}|-])/g, "\\$1").replace(/%/g,'[\\w\\d\\-_]+');
                    searchPath = new RegExp(searchPath+'$');
                    for( var i in cache ) // match path plz
                        if( cache[i].get('Path').search(searchPath) === 0 )
                            results.push(cache[i]);
                    return results;    
                },
                cachedResults = searchCache();
                
            if( cachedResults.length === 0 )
            {
                actions
                    .sync({data: {path: path}})
                    .done(function()
                    { 
                        actions.each(function(){ cache[this.get('Path')] = this; });
                        dfd.resolve(searchCache());
                    })
                    .fail(function(){ dfd.reject(); });
                return dfd;
            }
            return dfd.resolve(cachedResults);
        },
        
        /*!
         * get one action from a path
         */
        get: function(path, url)
        {
            var dfd = new $.Deferred;
            if( !cache[path] )
            {
                var searchPath = path.substr(0, path.lastIndexOf('.'));
                actions.sync({data: {path: searchPath+'.*'}})
                    .done(function()
                    { 
                        actions.each(function(){ cache[this.get('Path')] = this; });
                        cache[path] && dfd.resolve(cache[path]);
                        dfd.reject();
                    });
                return dfd;
            }
            return dfd.resolve(cache[path]);
        },
           
        /*!
         * get a bunch of scripts from a path and initialize them
         * @param string path
         */
        initApps: function(path)
        {
            var args = []; 
            Array.prototype.push.apply( args, arguments );
            args.shift();
            return this.getMore(path).done(function( apps )
            {
                for( var i=0; i<apps.length; i++ )
                {
                    apps[i].get('Script') && require([apps[i].get('Script').href], function(app)
                    {
                        app && app.init && app.init.apply( app, args );
                    });
                }
            });
        },
        initApp: function(path)
        {
            var args = []; 
            Array.prototype.push.apply( args, arguments );
            args.shift();
            return this.get(path).done(function( app )
            { 
                app.get('Script') && require([app.get('Script').href], function(app)
                {
                    app && app.init && app.init.apply( app, args );
                }); 
            })
        }
           
    };
    
    return gizmo.Superdesk.action;
});