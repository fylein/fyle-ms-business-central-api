# Generated by Django 4.1.2 on 2024-01-11 10:18

from django.db import migrations, models
import django.db.models.deletion
import ms_business_central_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounting_exports', '0001_initial'),
        ('workspaces', '0003_rename_default_journal_entry_folder_id_exportsetting_journal_entry_folder_id_and_more'),
        ('fyle', '0001_initial'),
        ('business_central', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('accounting_date', ms_business_central_api.models.fields.CustomDateTimeField(help_text='accounting date of purchase invoice', null=True)),
                ('amount', ms_business_central_api.models.fields.FloatNullField(help_text='Total Amount of the invoice', null=True)),
                ('code', ms_business_central_api.models.fields.StringNullField(help_text='unique code for invoice', max_length=10, null=True)),
                ('description', ms_business_central_api.models.fields.TextNotNullField(help_text='description for the invoice')),
                ('invoice_date', ms_business_central_api.models.fields.CustomDateTimeField(help_text='date of invoice', null=True)),
                ('vendor_number', ms_business_central_api.models.fields.StringNullField(help_text='id of vendor', max_length=255, null=True)),
                ('accounting_export', models.OneToOneField(help_text='Accounting Export reference', on_delete=django.db.models.deletion.PROTECT, to='accounting_exports.accountingexport')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'purchase_invoices',
            },
        ),
        migrations.AddField(
            model_name='journalentry',
            name='employee_account_id',
            field=ms_business_central_api.models.fields.StringNullField(help_text='destination id of employee account', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='journalentrylineitems',
            name='employee_account_id',
            field=ms_business_central_api.models.fields.StringNullField(help_text='destination id of employee account', max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='PurchaseInvoiceLineitems',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('accounts_payable_account_id', ms_business_central_api.models.fields.StringNullField(help_text='destination id of accounts payable account', max_length=255, null=True)),
                ('amount', ms_business_central_api.models.fields.FloatNullField(help_text='Amount of the invoice', null=True)),
                ('description', ms_business_central_api.models.fields.TextNotNullField(help_text='description for the invoice')),
                ('expense', models.OneToOneField(help_text='Reference to Expense', on_delete=django.db.models.deletion.PROTECT, to='fyle.expense')),
                ('purchase_invoice', models.ForeignKey(help_text='Reference to PurchaseInvoice', on_delete=django.db.models.deletion.PROTECT, to='business_central.purchaseinvoice')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'purchase_invoice_lineitems',
            },
        ),
    ]