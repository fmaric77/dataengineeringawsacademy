1. Zero-Shot and Few-Shot Prompts
1.a) Simplify this sentence: 'The meteorological conditions are favorable today.'
Zero-Shot: The weather is good today.
Few-Shot:
Input 1: "The temperature is quite low today." → Simplified: "It's cold today."
Input 2: "The atmospheric pressure is high." → Simplified: "Pressure is high."
Output: The weather is nice today.
1.b) Write a formal greeting for an email to a professor.
Zero-Shot: Dear Professor [Last Name],
Few-Shot:
Input 1: "Write a greeting for an email to a boss." → Output: "Dear Sir/Madam,"
Input 2: "Write a greeting for an email to a colleague." → Output: "Hello [Name],"
Output: Dear Professor [Last Name],
1.c) Generate a list of countries.
Zero-Shot:
United States
Canada
Germany
Japan
Brazil
Few-Shot:
Input 1: "Generate a list of European countries." → Output: "France, Germany, Spain, Italy."
Input 2: "Generate a list of Asian countries." → Output: "China, India, Japan, South Korea."
Output:
United States
Canada
Germany
Japan
Brazil
2. Chain-of-Thought Prompts
2.a) John has 3 bags with 5 apples each. He buys 2 more apples. How many apples does he have in total?
Output:

John has 3 bags with 5 apples each.
3 bags × 5 apples = 15 apples.
He buys 2 more apples.
15 apples + 2 apples = 17 apples.
Total: John has 17 apples.
2.b) Explain the causes of World War I step by step.
Output:

Militarism: European nations built up large armies and navies, increasing tensions.
Alliances: Complex alliances formed between countries, meaning a conflict involving one nation could quickly involve others.
Imperialism: Competition for colonies created friction among the major powers.
Nationalism: Intense national pride and rivalries increased hostilities.
Assassination: The assassination of Archduke Franz Ferdinand of Austria-Hungary by a Serbian nationalist triggered the conflict.
Domino Effect: Austria-Hungary declared war on Serbia, and the alliance system led other nations to join, escalating the conflict into a world war.
3. Self-Consistency Prompt
Prompt: You have a shopping list with the following items and their prices:

3 apples at $2 each
2 loaves of bread at $3 each
4 cans of soup at $1.50 each
Calculate the total cost of the shopping list.

Process:

Calculate the cost of the apples:
3 apples × $2 = $6.
Calculate the cost of the bread:
2 loaves of bread × $3 = $6.
Calculate the cost of the soup:
4 cans of soup × $1.50 = $6.
Add up all the costs:
$6 (apples) + $6 (bread) + $6 (soup) = $18.
Final Answer: The total cost of the shopping list is $18.