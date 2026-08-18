SUPPORTED=("dnd","mystara","mausritter","forbidden_lands","the_one_ring","gurps","worlds_without_number","stars_without_number","cities_without_number","ashes_without_number","tales_from_the_loop","traveller_2e")

class AdapterRegistry:
    def __init__(self): self._items={k:{"system_id":k} for k in SUPPORTED}
    def get(self,system_id):
        if system_id not in self._items: raise KeyError(system_id)
        return self._items[system_id]
