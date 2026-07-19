def num_to_words(number: float) -> str:
    """
    Converts a float number to standard Indian Rupees format in words.
    E.g. 12345.50 -> "Twelve Thousand Three Hundred Forty Five Rupees and Fifty Paise Only"
    """
    if number < 0:
        return "Negative value not supported"
    
    # Split rupees and paise
    parts = f"{number:.2f}".split('.')
    rupees = int(parts[0])
    paise = int(parts[1])
    
    def convert_below_thousand(num):
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", 
                 "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        if num == 0:
            return ""
        
        words = []
        if num >= 100:
            words.append(units[num // 100])
            words.append("Hundred")
            num %= 100
            
        if num >= 20:
            words.append(tens[num // 10])
            num %= 10
            
        if num > 0:
            words.append(units[num])
            
        return " ".join(words)
        
    def convert_rupees(num):
        if num == 0:
            return "Zero"
            
        words = []
        
        # Crores (1,00,00,000)
        crores = num // 10000000
        if crores > 0:
            words.append(convert_below_thousand(crores))
            words.append("Crore")
            num %= 10000000
            
        # Lakhs (10,00,00)
        lakhs = num // 100000
        if lakhs > 0:
            words.append(convert_below_thousand(lakhs))
            words.append("Lakh")
            num %= 100000
            
        # Thousands (1,000)
        thousands = num // 1000
        if thousands > 0:
            words.append(convert_below_thousand(thousands))
            words.append("Thousand")
            num %= 1000
            
        # Hundreds and tens
        if num > 0:
            words.append(convert_below_thousand(num))
            
        return " ".join([w for w in words if w])

    rupees_str = convert_rupees(rupees)
    paise_str = convert_below_thousand(paise)
    
    result = f"{rupees_str} Rupees"
    if paise > 0:
        result += f" and {paise_str} Paise"
    result += " Only"
    
    # Clean multiple spaces
    return " ".join(result.split())
