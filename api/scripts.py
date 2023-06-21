from api.models import Turn
from datetime import date, datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User

def generate_turns(start_date = date.today().strftime("%d/%m/%y")):

    for x in User.objects.filter(profile__type_id="2002"):
        try:
            turns = settings.TURNS_TIMES[x.profile.turn_time]
        except:
            print("Exception: No setting on therapist turn time")

        for t in turns:
            try:
                date_str = f'{start_date} {t}'
                final_date = datetime.strptime(date_str, '%d/%m/%y %H:%M:%S')
            except:
                print("Exception: Date start not valid")

            turn = Turn(
                start_time=final_date,
                end_time=(final_date + timedelta(minutes=29)),
                therapist=x
            )
            turn.save()
    print("Turns created")