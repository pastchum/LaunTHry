from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, CallbackContext
from uuid import uuid4

import threading
import time

TOKEN = BOT TOKEN

#commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, thank you for using our bot. Please use \n' +
                                     '/check to see which machines are being used, \n' + 
                                     '/using to declare if you are using a machine and \n' +
                                     '/cancel to cancel your declaration of usage')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, here are the available commands for the bot! \n' + 
                                    '/start - start the bot \n' + 
                                    '/check - check what machines are available in each block \n' + 
                                    '/using - declare your usage of a machine\n'
                                    '/cancel - undo declaring your usage of a machine')

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['command'] = '/check'
    keyboard = [
        [InlineKeyboardButton(block, callback_data=block)] for block in block_instances.keys()
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose your block:', reply_markup=reply_markup)

async def using_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['command'] = '/using'
    keyboard = [
        [InlineKeyboardButton(block, callback_data=block)] for block in block_instances.keys()
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose your block:', reply_markup=reply_markup)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['command'] = '/cancel'
    keyboard = [
        [InlineKeyboardButton(block, callback_data=block)] for block in block_instances.keys()
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose your block:', reply_markup=reply_markup)

#responses
async def check_options(update, context):
    query = update.callback_query
    option = query.data
    if '_' not in option:
        blk_machines = block_instances[option].machines  # List of machines
        available_machines_names = []
        available_machines = []
        unavailable_machines_names = []
        unavailable_machines = []
        for machine in blk_machines:
            if not machine.used:
                available_machines_names.append(machine.name + '\n')
                available_machines.append(machine)
            else:
                unavailable_machines_names.append(machine.name + '\n')
                unavailable_machines.append(machine)

    if context.user_data.get('command') == '/check':
        avail_text = f'Available Machines:\n{"".join(available_machines_names)}'
        unavail_text = f'Unvailable Machines:\n{"".join(unavailable_machines_names)}'
        if available_machines:
            reply_text = avail_text + "\n" + unavail_text
        else:
            reply_text = 'No available machines' + "\n" + unavail_text
        await query.message.reply_text(reply_text)
        
    elif context.user_data.get('command') == '/using':
        context.user_data['command'] = 'selected'
        if available_machines:
            keyboard = [
                [InlineKeyboardButton(machine.name, callback_data=f'{machine.block.block}_{machine.name}')] for machine in available_machines
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('Please choose the machine you are using:', reply_markup=reply_markup)
        else:
            await query.message.reply_text('No available Machines')
    
    elif context.user_data.get('command') == '/cancel':
        context.user_data['command'] = 'selected'
        if unavailable_machines:
            keyboard = [
                [InlineKeyboardButton(machine.name, callback_data=f'{machine.block.block}_{machine.name}')] for machine in unavailable_machines
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('Please choose the machine you are using:', reply_markup=reply_markup)
        else:
            await query.message.reply_text('All Machines available')

    elif context.user_data.get('command') == 'selected':
        query = update.callback_query
        option = query.data #machine blk + name
        machine_blk, machine_name = option.split('_')[0], option.split('_')[1]
    
        # Find the corresponding machine
        selected_machine = None
        for machine in block_instances[machine_blk].machines:
            if machine.name == machine_name:
                selected_machine = machine
                break

        # Set machine as used
        selected_machine.update()
        if selected_machine.used:
            await query.message.reply_text(f'You selected machine: {machine_name}. It is now marked as used.')

        else:
            selected_machine.cancel_timer()
            await query.message.reply_text(f'You selected machine: {machine_name}. It is now marked as free.')
        # Provide feedback to the user

async def inlinequery(update: Update, context: CallbackContext):
    query = update.inline_query.query
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=block,
            input_message_content=InputTextMessageContent(query),
        )
        for block in block_instances.keys()
    ]
    await update.inline_query.answer(results)

#classes
class machine:
    def __init__(self, type, name, blk):
        self.type = type
        self.used = False
        self.name = name
        self.block = blk
        self.timer = None
        self.elapsed_time = 0

    def update(self):
        if self.used:
            self.used = False
        else:
            self.used = True

    def start_timer(self, duration):
        self.elapsed_time = 0
        self.timer = threading.Timer(duration)
        self.timer.start()

    def cancel_timer(self):
        if self.timer:
            self.timer.cancel()
            print("Timer canceled.")

    def get_elapsed_time(self):
        return (1800 - self.elapsed_time)/60

class block:
    def __init__(self, block) -> None:
        self.block = block
        self.machines = []

    def add_washer(self, washer_name):
        washer = machine("washer", washer_name, self)
        self.machines.append(washer)

    def add_dryer(self, dryer_name):
        dryer = machine("dryer", dryer_name, self)
        self.machines.append(dryer)

blk_a = block("A")
blk_b = block("B")
blk_c = block("C")
blk_d = block("D")
blk_e = block("E")
block_instances = {'A': blk_a, 'B': blk_b, 'C': blk_c, 'D': blk_d, 'E': blk_e}
for blk in block_instances.values():
    blk.add_dryer("dryer1")
    blk.add_dryer("dryer2")
    blk.add_washer("washerA1")
    blk.add_washer("washerA2")
    blk.add_washer("washerA3")
    blk.add_washer("washerB1")
    blk.add_washer("washerB2")
    blk.add_washer("washerB3")

#main
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    #commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('check', check_command))
    app.add_handler(CommandHandler('using', using_command))
    app.add_handler(CommandHandler('cancel', cancel_command))

    app.add_handler(CallbackQueryHandler(check_options)) 
    #run
    app.run_polling(poll_interval=1)

if __name__ == '__main__':
    main()
