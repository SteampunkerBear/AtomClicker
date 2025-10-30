from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect,HttpResponseBadRequest,FileResponse, Http404, JsonResponse
from django.urls import reverse
from django.db import IntegrityError
from .models import User
from django.contrib.auth.decorators import login_required
# Create your views here.
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = "noemail@email.com"
        if len(username) > 30:
          return render(request, "register.html", {
                "message": "Username too long"
            })
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "register.html")

# intializes all the goodies
def initialize_session_defaults(session):
    defaults = {
        "base_gain": 1,
        "plus_one_cost": 10,
        "gain_multiplier": 1,
        "times_two_cost": 1000,
        "times_two_level": 0,
        "auto_clicker_active": False,
        "auto_clicker_gain": 1,
        "model_multiplier": 1,
        "model_right_now": "dalton",
        "model_thomson_purchased": False,
        "model_rutherford_purchased": False,
        "model_bohr_purchased": False,
        "model_current_purchased": False,
        "just_upgraded_thomson": False,
        "just_upgraded_rutherford": False,
        "just_upgraded_bohr": False,
        "just_upgraded_current": False
    }  # ✅ dictionary ends here

    # ✅ now the loop runs after the dictionary is defined
    for key, value in defaults.items():
        if key not in session:
            session[key] = value

#RESTART BUTTON
def restart(request):
    if request.method=="POST":
        request.user.point = 0 
        request.session["atom_gain"] = 1
        request.session["plus_one_cost"] = 10
        request.session["times_two_cost"] = 1000
        request.session["base_gain"] = 1
        request.session["gain_multiplier"] = 1
        request.session["times_two_level"] = 0
        request.session["auto_clicker_active"] = False
        request.session["auto_clicker_gain"] = 1
        request.session["model_right_now"] = "dalton"
        #RESETS MODELS
        request.session["model_thomson_purchased"] = False
        request.session["model_rutherford_purchased"] = False
        request.session["model_bohr_purchased"] = False
        request.session["model_current_purchased"] = False
        request.session["model_multiplier"] = 1
        request.user.save()
        print("restart succesful")
    return redirect('index')

def apply_model_prestige(request, model_name, cost, flag_name):
    if request.user.point >= cost and not request.session.get(flag_name, False):
        # Reset upgrades
        request.session["atom_gain"] = 1
        request.session["plus_one_cost"] = 10
        request.session["times_two_cost"] = 1000
        request.session["times_two_level"] = 0
        request.session["auto_clicker_active"] = False
        request.session["auto_clicker_gain"] = 1
        request.session["base_gain"] = 1
        request.session["gain_multiplier"] = 1
        request.user.point = 0

        # Apply multiplier
        request.session["model_multiplier"] = request.session.get("model_multiplier", 1) * 2

        # Update model state
        request.session["model_right_now"] = model_name
        request.session[flag_name] = True
        request.user.save()
        return True
    return False

def auto_clicker_tick(request):

    if request.method == "POST" and request.session.get("auto_clicker_active"):
        base_gain = request.session.get("base_gain", 1)
        gain_multiplier = request.session.get("gain_multiplier", 1)
        model_multiplier = request.session.get("model_multiplier", 1)

        atom_gain = base_gain * gain_multiplier * model_multiplier

        multiplier = request.session.get("model_multiplier", 1)
        gain = atom_gain * multiplier
        request.user.point += gain
        request.user.save()

        return JsonResponse({"point": request.user.point})

    return JsonResponse({"point": request.user.point})

def click_atom(request):
    if request.method == "POST":
        atom_gain = request.session.get("atom_gain", 1)
        multiplier = request.session.get("model_multiplier", 1)
        gain = atom_gain * multiplier

        request.user.point += gain
        request.user.save()

        return JsonResponse({"point": request.user.point})
    return JsonResponse({"error": "Invalid request"})

def game_broken(request):
    return render(request, "game_broken.html")

@login_required(login_url='login')

def index(request):
 
    initialize_session_defaults(request.session)

    just_upgraded_thomson = request.session.pop("just_upgraded_thomson", False)
    just_upgraded_rutherford = request.session.pop("just_upgraded_rutherford", False)
    just_upgraded_bohr = request.session.pop("just_upgraded_bohr", False)
    just_upgraded_current = request.session.pop("just_upgraded_current", False)

    atom_gain = request.session["base_gain"] * request.session["gain_multiplier"] * request.session["model_multiplier"] 
    
    try:
        if atom_gain > 2**31 - 1:
            return redirect("game_broken")
    except (KeyError, OverflowError, ValueError):
        return redirect("game_broken")
    if request.method=="POST":
        user_action = request.POST.get("action")
        if user_action == "click":

            request.user.point += atom_gain
            request.user.save()
            point = request.user.point
        elif user_action == "upgrade_gain":
            upgrade_name = request.POST.get("upgrade_name")
            if upgrade_name == "plus_one":
                #Increase atom gain per click
                cost = request.session["plus_one_cost"]
                if request.user.point >= cost: 
                    request.user.point -= cost
                    request.session["base_gain"] += 1
                    request.session["plus_one_cost"] = int(cost**1.05) #Increase cost
                    request.user.save()
                    return redirect('index')
                else:
                    pass
            elif upgrade_name == "times_two":
                #Increase atmo gain by a factor of 2
                mult_cost = request.session["times_two_cost"]
                level = request.session.get("times_two_level", 0)

                if request.user.point >= mult_cost:
                    request.user.point -= mult_cost
                    request.session["gain_multiplier"] *= 2
                    request.session["times_two_level"] = level + 1
                    
                    #recalculate cost using exponential scales!!!!
                    new_level = level + 1
                    request.session["times_two_cost"] = int(1000 * (1.5 ** new_level)) #Increase cost
                    request.user.save()
                    return redirect('index')
                else:
                    pass
            elif upgrade_name == "auto_clicker":
                # Start auto-clicker
                clicker_cost = 100
                if request.user.point >= clicker_cost and not request.session.get("auto_clicker_active", False):
                    request.user.point -= clicker_cost
                    request.session["auto_clicker_active"] = True
                    request.session["auto_clicker_gain"] = atom_gain#number of atoms per tick
                    request.user.save()
                else:
                    pass
                
        elif user_action == "upgrade_model":

            upgrade_name = request.POST.get("upgrade_name")

            if upgrade_name == "thomson" and request.session["model_right_now"] == "dalton":
                if apply_model_prestige(request, "thomson", 5000, "model_thomson_purchased"):
                    request.session["just_upgraded_thomson"] = True
                    return redirect('index')

            elif upgrade_name == "rutherford" and request.session["model_right_now"] == "thomson":
                if apply_model_prestige(request, "rutherford", 50000, "model_rutherford_purchased"):
                    request.session["just_upgraded_rutherford"] = True
                    return redirect('index')

            elif upgrade_name == "bohr" and request.session["model_right_now"] == "rutherford":
                if apply_model_prestige(request, "bohr", 500000, "model_bohr_purchased"):
                    request.session["just_upgraded_bohr"] = True
                    return redirect('index')

            elif upgrade_name == "current" and request.session["model_right_now"] == "bohr":
                if apply_model_prestige(request, "current", 10000000, "model_current_purchased"):
                    request.session["just_upgraded_current"] = True
                    return redirect('index')
     # Choose image based on point count
    model = request.session["model_right_now"]
    point = request.user.point
    if model == "dalton":
        image_path = "images/black_sphere.png"
        button_text = "Dalton model"
        fun_fact = "FUN FACT ABOUT DALTON: Dalton helped further research on color blindness by donating his eyes after his death. Dalton believed that the liquid behind your eye was a filter for colors and that he was missing something since he couldn’t see all colors. After the autopsy it was discovered that the liquid was colorless meaning his theory was wrong. However DNA analysis shows that Dalton was missing a receptor for green."
        info_on_model = "THE DALTON MODEL: John Dalton was the first scientist to create a modern atomic theory, which stated that atoms are the smallest forms of elements, atoms of the same element have the same atomic mass, and thus atoms of different elements have different masses. The Dalton model only has a nucleus."
    elif model == "thomson":
        image_path = "images/thomson.png"
        button_text = "Thomson model"
        fun_fact = "FUN FACT ABOUT THOMSON: J. J. Thomson received the Nobel Prize in Physics in 1906, and so did his son, George Paget Thomson, in 1937.  He worked as a master for Trinity College, and a total of seven Nobel Prizes were awarded those who worked under him."
        info_on_model = "THE THOMSON MODEL: J. J. Thomson’s atomic theory is known as the Plum Pudding model, proposing that atoms are spheres of positive charge with electrons contained inside.  He came up with this model because he observed that cathode rays (electrons) were negatively charged, so the rest of the atom must be positive to make the atom neutral."
    elif model == "rutherford":
        image_path = "images/rutherford.png" 
        button_text = "Rutherford model"
        fun_fact = "FUN FACT ABOUT RUTHERFORD: Rutherford is known as the father of nuclear physics, discovering concepts such as radioactive half-life, alpha and beta radiation, and radon.  Rutherford’s face is featured on the front of the New Zealand $100 bill, and element 104, rutherfordium, is named after him."
        info_on_model = "THE RUTHERFORD MODEL: Ernest Rutherford was the creator of the nuclear model, showing that an atom consists of a small, dense, positively charged nucleus that is surrounded by orbiting electrons and mostly empty space.  Rutherford came to this conclusion after observing how positively charged alpha particles passed through gold foil, but a few were deflected by presumably small particles with a positive charge."
    elif model == "bohr":
        image_path = "images/bohr.png"
        button_text = "Bohr model"
        fun_fact = "FUN FACT ABOUT BOHR: Bohr played goalkeeper on a competitive soccer team with his brother, who won an Olympic silver medal.  Just like Thomson, Bohr’s son, Aage N. Bohr won a Nobel Prize in Physics in 1975, and the element bohrium was named in his honor."
        info_on_model = "THE BOHR MODEL: Neils Bohr improved off of Rutherford’s model by addressing how electrons fit in the atomic model.  Bohr’s model says that electrons travel in specific orbits around the nucleus, and electrons can absorb or emit energy in order to jump to a different energy level or shell.  Bohr observed this emission of energy in the form of light, and the fact that different elements when heated emitted different wavelengths suggested that different elements had different energy amounts per level and interval/jump."

    elif model == "current":
        image_path = "images/modern.png"
        button_text = "Modern model"
        fun_fact = "FUN FACT ABOUT SCHRODINGER, EINSTEN, AND HEISENBERG: Schrodinger would tell people that asked him if the cat was alive or dead that they should ask the cat. Einsten really enjoyed sailing however he was not too skilled and capsized multiple times. Schrodinger also made a book What is Life? that inspired the discovery of DNA, Watson and Crick credited him with his ideas. Heseinberg might've taught Nazi soldiers quantum mechanics through a spinning top because Nazis thought the theories might be fake."
        info_on_model = "THE CURRENT MODEL: When Erwin Schrödinger began his work (around 1925–1926), Niels Bohr’s atomic model (1913) was still the best available theory to describe the structure of the atom. Bohr’s model explained the hydrogen atom’s spectral lines using quantized orbits — electrons moving in fixed circular paths around the nucleus. He was able to verify the energy levels using the new method and found that they catch up with Bohr. Schrödinger transformed Bohr’s discrete orbits into wave-like probability clouds."
    return render(request, 'index.html', {
        'point': point,
        'image_path': image_path,
        'button_text' : button_text,
        'fun_fact' : fun_fact,
        'info_on_model' : info_on_model,
        'atom_gain': atom_gain,
        'plus_one_cost': request.session["plus_one_cost"],
        'times_two_cost': request.session["times_two_cost"],
        'auto_clicker_active': request.session.get("auto_clicker_active", False),
        'model_right_now': request.session.get("model_right_now"),
        'model_thomson_purchased': request.session.get("model_thomson_purchased", False),
        'model_rutherford_purchased': request.session.get("model_rutherford_purchased", False),
        'model_bohr_purchased': request.session.get("model_bohr_purchased", False),
        'model_current_purchased': request.session.get("model_current_purchased", False),
        'model_multiplier': request.session.get("model_multiplier", 1),
        'just_upgraded_thomson': just_upgraded_thomson,
        'just_upgraded_rutherford': just_upgraded_rutherford,
        'just_upgraded_bohr': just_upgraded_bohr,
        'just_upgraded_current': just_upgraded_current,
        })

