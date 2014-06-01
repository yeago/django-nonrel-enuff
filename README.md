> Omg should my projeKtt go Nonrel to achieve webspeed?? How can I mongo? Plz advize.

## Meh, no.

Just use this handy manager situationally, mostly when you want to stuff the latest X things onto some arbitrary list.

    class Comment(models.Model) 
       ...
       nonrel_objects = EnuffManager()

Later that that year, <s>someone</s> a bot spammer saves a comment on your shitty blog which you should have just used WordPress but were too smug about your great python skills and now you're maintaining your dumb blog app that nobody else uses or cares about because they are too busy maintaining their own shittier one (haha, just kidding, yours is the worst).

    def some_save_signal(instance, *wtvr) 
       Comment.nonrel_objects.push_to_list('latest-comments', instance, trim=50)

Two years later, someone visits your fucking pedantic blog and then this happens 

    def my_homepage_view(request) 
       .... # blah blah blah
       context = {
          'latest_comments':  Comment.nonrel_objects.get_list('latest_comments')
       }
       .... # blah blah eventually a regrettable response is returned


But your bounce rate is 95% so the comment doesn't even load, but still. It was efficient and you finally did webspeed. Or what's more likely is heroku broke one of their internal APIs like they do every 6 months so you got a 500, but at least the comment was somewhere in memory.

## Advantages (not really a numerical list)

1. Just stop writing migrations everytime you need a new feed. Stuff them into another queue. Keep that queue trimmed to a reasonable size and go outside on the weekend instead of trying to figure out why in the world MySQL wont use the right index on your sub-select of 50 million comments just to get the latest 5 related to some object.

## Supported Backends

1. Redis
2. Something else some other person decides to write (mongo pull requests ignored)
