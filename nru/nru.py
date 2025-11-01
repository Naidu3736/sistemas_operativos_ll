import sys 
from mmu import MMU

class NRU:
    def __init__(self, reset_interval = 1000):
        self.reference_count = 0
        self.reset_interval = reset_interval

    def _classify_page(self, mmu : MMU, page):
        r = mmu.get_reference_bit(page)
        m = mmu.get_modified_bit(page)

        if not r and not m:
            return 0
        if not r and m:
            return 1
        if r and not m:
            return 2
        if r and m:
            return 3
        
    def _reset_reference_bits_if_needed(self, mmu : MMU):
        self.reference_count += 1

        if self.reference_count >= self.reset_interval:
            self.reference_count = 0
            mmu.clear_all_reference_bits()

    def select_victim(self, mmu : MMU):
        self._reset_reference_bits_if_needed(mmu)

        present_pages = mmu.get_present_pages()
        if not present_pages:
            return None
        
        classes = {0:[], 1:[], 2:[], 3:[]}
        for page in present_pages:
            page_class = self._classify_page(mmu, page)
            classes[page_class].append(page)

        for class_num in range(4):
            if classes[class_num]:
                return classes[class_num][0]
            
        return present_pages[0]
    
    def page_reference(self):
        self.reference_count += 1
    



        