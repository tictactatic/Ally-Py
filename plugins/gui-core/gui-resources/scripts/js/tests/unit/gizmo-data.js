define(function()
{
    return {
        ajaxMap: {
            'Collaborator/1': 
            {
                "Source": {"href": "Source/1", "Id": "1"}, 
                "Person": {"href": "Person/1", "Id": "1"},
                "Post": {"href": "Collaborator/1/Post"},
                "PostPublished": {"href": "Collaborator/1/Post/Published"},
                "PostUnpublished": {"href": "Collaborator/1/Post/Unpublished"}, 
                "Id": "1", "Name": "Test User"
            },
            "Collaborator/1/Post":
            {
                "PostList": 
                [
                    {
                        "href": "Post/1", 
                        "Author": { "href": "Collaborator/1/", "Id": "1" }, 
                        "CreatedOn": "Jun 5, 2012 5:50:49 PM", 
                        "Creator": { "href": "User/1", "Id": "1" }, 
                        "Content": "GEN Live Desk is a next-generation open source web tool for both individuals and teams to report live breaking news from anywhere.", 
                        "AuthorName": "Author 1", 
                        "PublishedOn": "Jun 5, 2012 5:50:49 PM", 
                        "Type": { "href": "PostType/quote", "Key": "quote" }, 
                        "Id": "1", 
                        "IsModified": "False"
                    }, 
                    {   
                        "href": "Post/2", 
                        "Author": { "href": "Collaborator/1", "Id": "1" }, 
                        "CreatedOn": "Jun 5, 2012 5:50:50 PM", 
                        "Creator": { "href": "User/1", "Id": "1" }, 
                        "Content": "That is all for today folks. Join us at GEN News World Media Summit to see Douglas Arellanes demoing the tool live.", 
                        "AuthorName": "User2", 
                        "PublishedOn": "Jun 5, 2012 5:50:50 PM",
                        "Type": { "href": "PostType/wrapup", "Key": "wrapup" }, 
                        "Id": "2", 
                        "IsModified": "False"
                    }
                ], 
                "total": "2"
            },
            "Collaborator/1/Post/Published":
            {
                
            },
            "Collaborator/1/Post/Unpublished":
            {
                
            },
            
            
            "Source/1": 
            {
                "Name": "internal", 
                "URI": {"href": ""}, 
                "IsModifiable": "False", 
                "Collaborator": {"href": "Source/1/Collaborator"}, 
                "Type": {"href": "SourceType/", "Key": ""}, 
                "Id": "2"
            },
            "Source/1/Collaborator": 
            {
                
            },
            
            "Person/1":
            {
                "Collaborator": {"href": "Person/1/Collaborator"}, 
                "FullName": "Test Person", 
                "Id": "1", 
                "FirstName": "Person", 
                "EMail": "person@email.com"
            },
            "Person/1/Collaborator":
            {
                
            }
        }
    };
});