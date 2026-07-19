export function numberToWords(number) {
  if (number === undefined || number === null || isNaN(number)) return '';
  if (number < 0) return 'Negative value not supported';
  
  const parts = parseFloat(number).toFixed(2).split('.');
  const rupees = parseInt(parts[0], 10);
  const paise = parseInt(parts[1], 10);
  
  function convertBelowThousand(num) {
    const units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", 
                   "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
    const tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];
    
    if (num === 0) return "";
    
    let words = [];
    if (num >= 100) {
      words.push(units[Math.floor(num / 100)]);
      words.push("Hundred");
      num %= 100;
    }
    
    if (num >= 20) {
      words.push(tens[Math.floor(num / 10)]);
      num %= 10;
    }
    
    if (num > 0) {
      words.push(units[num]);
    }
    
    return words.join(" ");
  }
  
  function convertRupees(num) {
    if (num === 0) return "Zero";
    
    let words = [];
    
    // Crores
    const crores = Math.floor(num / 10000000);
    if (crores > 0) {
      words.push(convertBelowThousand(crores));
      words.push("Crore");
      num %= 10000000;
    }
    
    // Lakhs
    const lakhs = Math.floor(num / 100000);
    if (lakhs > 0) {
      words.push(convertBelowThousand(lakhs));
      words.push("Lakh");
      num %= 100000;
    }
    
    // Thousands
    const thousands = Math.floor(num / 1000);
    if (thousands > 0) {
      words.push(convertBelowThousand(thousands));
      words.push("Thousand");
      num %= 1000;
    }
    
    if (num > 0) {
      words.push(convertBelowThousand(num));
    }
    
    return words.filter(w => w !== "").join(" ");
  }

  const rupeesStr = convertRupees(rupees);
  const paiseStr = convertBelowThousand(paise);
  
  let result = `${rupeesStr} Rupees`;
  if (paise > 0) {
    result += ` and ${paiseStr} Paise`;
  }
  result += " Only";
  
  return result.replace(/\s+/g, ' ').trim();
}
