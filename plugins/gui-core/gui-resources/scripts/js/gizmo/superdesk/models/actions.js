define(['gizmo/superdesk', 'gizmo/superdesk/models/action'], function(Gizmo, Action)
{
    var actionUrl = Gizmo.Url.extend
    ({
        get: function()
        {
            var login = localStorage.getItem('superdesk.login.selfHref')+'/Action';
            this.data.url = login ? login : 'GUI/Action';
            this.data.root = login ? '' : Gizmo.Url.prototype.data.root;
            return Gizmo.Url.prototype.get.apply(this, arguments);
        }
    });
    return Gizmo.Collection.extend({ model: Action, url: new actionUrl('GUI/Action'), syncAdapter: Gizmo.AuthSync });
});